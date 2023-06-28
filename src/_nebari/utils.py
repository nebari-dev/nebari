import contextlib
import functools
import hashlib
import os
import pathlib
import re
import signal
import subprocess
import sys
import threading
import time
from typing import Dict, List

from rich.table import Table
from ruamel.yaml import YAML

from _nebari.provider.cloud import (
    amazon_web_services,
    azure_cloud,
    digital_ocean,
    google_cloud,
)
from nebari import schema

# environment variable overrides
NEBARI_K8S_VERSION = os.getenv("NEBARI_K8S_VERSION", None)
NEBARI_GH_BRANCH = os.getenv("NEBARI_GH_BRANCH", None)

DO_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-do"
AWS_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-aws"
GCP_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-gcp"
AZURE_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-azure"

CONDA_FORGE_CHANNEL_DATA_URL = "https://conda.anaconda.org/conda-forge/channeldata.json"

# Create a ruamel object with our favored config, for universal use
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False


@contextlib.contextmanager
def timer(logger, prefix):
    start_time = time.time()
    yield
    logger.info(f"{prefix} took {time.time() - start_time:.3f} [s]")


@contextlib.contextmanager
def change_directory(directory):
    current_directory = os.getcwd()
    os.chdir(directory)
    yield
    os.chdir(current_directory)


def run_subprocess_cmd(processargs, **kwargs):
    """Runs subprocess command with realtime stdout logging with optional line prefix."""
    if "prefix" in kwargs:
        line_prefix = f"[{kwargs['prefix']}]: ".encode("utf-8")
        kwargs.pop("prefix")
    else:
        line_prefix = b""

    timeout = 0
    if "timeout" in kwargs:
        timeout = kwargs.pop("timeout")  # in seconds

    strip_errors = kwargs.pop("strip_errors", False)

    process = subprocess.Popen(
        processargs,
        **kwargs,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    # Set timeout thread
    timeout_timer = None
    if timeout > 0:

        def kill_process():
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass  # Already finished

        timeout_timer = threading.Timer(timeout, kill_process)
        timeout_timer.start()

    for line in iter(lambda: process.stdout.readline(), b""):
        full_line = line_prefix + line
        if strip_errors:
            full_line = full_line.decode("utf-8")
            full_line = re.sub(
                r"\x1b\[31m", "", full_line
            )  # Remove red ANSI escape code
            full_line = full_line.encode("utf-8")

        sys.stdout.buffer.write(full_line)
        sys.stdout.flush()

    if timeout_timer is not None:
        timeout_timer.cancel()

    return process.wait(
        timeout=10
    )  # Should already have finished because we have drained stdout


def load_yaml(config_filename: pathlib.Path):
    """
    Return yaml dict containing config loaded from config_filename.
    """
    with config_filename.open() as f:
        config = yaml.load(f.read())

    return config


def backup_config_file(filename: pathlib.Path, extrasuffix: str = ""):
    if not filename.exists():
        return

    # Backup old file
    backup_filename = pathlib.Path(f"{filename}{extrasuffix}.backup")

    if backup_filename.exists():
        i = 1
        while True:
            next_backup_filename = pathlib.Path(f"{backup_filename}~{i}")
            if not next_backup_filename.exists():
                backup_filename = next_backup_filename
                break
            i = i + 1

    filename.rename(backup_filename)
    print(f"Backing up {filename} as {backup_filename}")


def check_cloud_credentials(config: schema.Main):
    if config.provider == schema.ProviderEnum.gcp:
        for variable in {"GOOGLE_CREDENTIALS"}:
            if variable not in os.environ:
                raise ValueError(
                    f"""Missing the following required environment variable: {variable}\n
                    Please see the documentation for more information: {GCP_ENV_DOCS}"""
                )
    elif config.provider == schema.ProviderEnum.azure:
        for variable in {
            "ARM_CLIENT_ID",
            "ARM_CLIENT_SECRET",
            "ARM_SUBSCRIPTION_ID",
            "ARM_TENANT_ID",
        }:
            if variable not in os.environ:
                raise ValueError(
                    f"""Missing the following required environment variable: {variable}\n
                    Please see the documentation for more information: {AZURE_ENV_DOCS}"""
                )
    elif config.provider == schema.ProviderEnum.aws:
        for variable in {
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        }:
            if variable not in os.environ:
                raise ValueError(
                    f"""Missing the following required environment variable: {variable}\n
                    Please see the documentation for more information: {AWS_ENV_DOCS}"""
                )
    elif config.provider == schema.ProviderEnum.do:
        for variable in {
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "SPACES_ACCESS_KEY_ID",
            "SPACES_SECRET_ACCESS_KEY",
            "DIGITALOCEAN_TOKEN",
        }:
            if variable not in os.environ:
                raise ValueError(
                    f"""Missing the following required environment variable: {variable}\n
                    Please see the documentation for more information: {DO_ENV_DOCS}"""
                )

        if os.environ["AWS_ACCESS_KEY_ID"] != os.environ["SPACES_ACCESS_KEY_ID"]:
            raise ValueError(
                f"""The environment variables AWS_ACCESS_KEY_ID and SPACES_ACCESS_KEY_ID must be equal\n
                See {DO_ENV_DOCS} for more information"""
            )

        if (
            os.environ["AWS_SECRET_ACCESS_KEY"]
            != os.environ["SPACES_SECRET_ACCESS_KEY"]
        ):
            raise ValueError(
                f"""The environment variables AWS_SECRET_ACCESS_KEY and SPACES_SECRET_ACCESS_KEY must be equal\n
                See {DO_ENV_DOCS} for more information"""
            )


def set_kubernetes_version(
    config, kubernetes_version, cloud_provider, grab_latest_version=True
):
    cloud_provider_dict = {
        "aws": {
            "full_name": "amazon_web_services",
            "k8s_version_checker_func": amazon_web_services.kubernetes_versions,
        },
        "azure": {
            "full_name": "azure",
            "k8s_version_checker_func": azure_cloud.kubernetes_versions,
        },
        "do": {
            "full_name": "digital_ocean",
            "k8s_version_checker_func": digital_ocean.kubernetes_versions,
        },
        "gcp": {
            "full_name": "google_cloud_platform",
            "k8s_version_checker_func": google_cloud.kubernetes_versions,
        },
    }
    cloud_full_name = cloud_provider_dict[cloud_provider]["full_name"]
    func = cloud_provider_dict[cloud_provider]["k8s_version_checker_func"]
    cloud_config = config[cloud_full_name]

    def _raise_value_error(cloud_provider, k8s_versions):
        raise ValueError(
            f"\nInvalid `kubernetes-version` provided: {kubernetes_version}.\nPlease select from one of the following {cloud_provider.upper()} supported Kubernetes versions: {k8s_versions} or omit flag to use latest Kubernetes version available."
        )

    def _check_and_set_kubernetes_version(
        kubernetes_version=kubernetes_version,
        cloud_provider=cloud_provider,
        cloud_config=cloud_config,
        func=func,
    ):
        region = cloud_config["region"]

        # to avoid using cloud provider SDK
        # set NEBARI_K8S_VERSION environment variable
        if not NEBARI_K8S_VERSION:
            k8s_versions = func(region)
        else:
            k8s_versions = [NEBARI_K8S_VERSION]

        if kubernetes_version:
            if kubernetes_version in k8s_versions:
                cloud_config["kubernetes_version"] = kubernetes_version
            else:
                _raise_value_error(cloud_provider, k8s_versions)
        elif grab_latest_version:
            cloud_config["kubernetes_version"] = k8s_versions[-1]
        else:
            # grab oldest version
            cloud_config["kubernetes_version"] = k8s_versions[0]

    return _check_and_set_kubernetes_version()


@contextlib.contextmanager
def modified_environ(*remove: List[str], **update: Dict[str, str]):
    """
    https://stackoverflow.com/questions/2059482/python-temporarily-modify-the-current-processs-environment/51754362
    Temporarily updates the ``os.environ`` dictionary in-place.

    The ``os.environ`` dictionary is updated in-place so that the modification
    is sure to work in all situations.

    :param remove: Environment variables to remove.
    :param update: Dictionary of environment variables and values to add/update.
    """
    env = os.environ
    update = update or {}
    remove = remove or []

    # List of environment variables being updated or removed.
    stomped = (set(update.keys()) | set(remove)) & set(env.keys())
    # Environment variables and values to restore on exit.
    update_after = {k: env[k] for k in stomped}
    # Environment variables and values to remove on exit.
    remove_after = frozenset(k for k in update if k not in env)

    try:
        env.update(update)
        [env.pop(k, None) for k in remove]
        yield
    finally:
        env.update(update_after)
        [env.pop(k) for k in remove_after]


def deep_merge(*args):
    """Deep merge multiple dictionaries.

    >>> value_1 = {
    'a': [1, 2],
    'b': {'c': 1, 'z': [5, 6]},
    'e': {'f': {'g': {}}},
    'm': 1,
    }

    >>> value_2 = {
        'a': [3, 4],
        'b': {'d': 2, 'z': [7]},
        'e': {'f': {'h': 1}},
        'm': [1],
    }

    >>> print(deep_merge(value_1, value_2))
    {'m': 1, 'e': {'f': {'g': {}, 'h': 1}}, 'b': {'d': 2, 'c': 1, 'z': [5, 6, 7]}, 'a': [1, 2, 3,  4]}
    """
    if len(args) == 0:
        return {}
    elif len(args) == 1:
        return args[0]
    elif len(args) > 2:
        return functools.reduce(deep_merge, args, {})
    else:  # length 2
        d1, d2 = args

    if isinstance(d1, dict) and isinstance(d2, dict):
        d3 = {}
        for key in d1.keys() | d2.keys():
            if key in d1 and key in d2:
                d3[key] = deep_merge(d1[key], d2[key])
            elif key in d1:
                d3[key] = d1[key]
            elif key in d2:
                d3[key] = d2[key]
        return d3
    elif isinstance(d1, list) and isinstance(d2, list):
        return [*d1, *d2]
    else:  # if they don't match use left one
        return d1


def inspect_files(
    output_base_dir: str,
    ignore_filenames: List[str] = None,
    ignore_directories: List[str] = None,
    deleted_paths: List[str] = None,
    contents: Dict[str, str] = None,
):
    """Return created, updated and untracked files by computing a checksum over the provided directory.

    Args:
        output_base_dir (str): Relative base path to output directory
        ignore_filenames (list[str]): Filenames to ignore while comparing for changes
        ignore_directories (list[str]): Directories to ignore while comparing for changes
        deleted_paths (list[str]): Paths that if exist in output directory should be deleted
        contents (dict): filename to content mapping for dynamically generated files
    """
    ignore_filenames = ignore_filenames or []
    ignore_directories = ignore_directories or []
    contents = contents or {}

    source_files = {}
    output_files = {}

    def list_files(
        directory: str, ignore_filenames: List[str], ignore_directories: List[str]
    ):
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ignore_directories]
            for file in files:
                if file not in ignore_filenames:
                    yield os.path.join(root, file)

    for filename in contents:
        if isinstance(contents[filename], str):
            source_files[filename] = hashlib.sha256(
                contents[filename].encode("utf8")
            ).hexdigest()
        else:
            source_files[filename] = hashlib.sha256(contents[filename]).hexdigest()

        output_filename = os.path.join(output_base_dir, filename)
        if os.path.isfile(output_filename):
            output_files[filename] = hash_file(filename)

    deleted_files = set()
    for path in deleted_paths:
        absolute_path = os.path.join(output_base_dir, path)
        if os.path.exists(absolute_path):
            deleted_files.add(path)

    for filename in list_files(output_base_dir, ignore_filenames, ignore_directories):
        relative_path = os.path.relpath(filename, output_base_dir)
        if os.path.isfile(filename):
            output_files[relative_path] = hash_file(filename)

    new_files = source_files.keys() - output_files.keys()
    untracted_files = output_files.keys() - source_files.keys()

    updated_files = set()
    for prevalent_file in source_files.keys() & output_files.keys():
        if source_files[prevalent_file] != output_files[prevalent_file]:
            updated_files.add(prevalent_file)

    return new_files, untracted_files, updated_files, deleted_paths


def hash_file(file_path: str):
    """Get the hex digest of the given file.

    Args:
        file_path (str): path to file
    """
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def gen_render_diff(new_files, untracted_files, updated_files, deleted_paths):
    if new_files:
        table = Table("The following files will be created:", style="deep_sky_blue1")
        for filename in sorted(new_files):
            table.add_row(filename, style="green")
        print(table)
    if updated_files:
        table = Table("The following files will be updated:", style="deep_sky_blue1")
        for filename in sorted(updated_files):
            table.add_row(filename, style="green")
        print(table)
    if deleted_paths:
        table = Table("The following files will be deleted:", style="deep_sky_blue1")
        for filename in sorted(deleted_paths):
            table.add_row(filename, style="green")
        print(table)
    if untracted_files:
        table = Table(
            "The following files are untracked (only exist in output directory):",
            style="deep_sky_blue1",
        )
        for filename in sorted(untracted_files):
            table.add_row(filename, style="green")
        print(table)
