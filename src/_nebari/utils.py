import contextlib
import functools
import os
import re
import secrets
import signal
import string
import subprocess
import sys
import threading
import time
import warnings
from pathlib import Path
from typing import Dict, List, Set

from ruamel.yaml import YAML

from _nebari import constants

# environment variable overrides
NEBARI_GH_BRANCH = os.getenv("NEBARI_GH_BRANCH", None)

AZURE_TF_STATE_RESOURCE_GROUP_SUFFIX = "-state"
AZURE_NODE_RESOURCE_GROUP_SUFFIX = "-node-resource-group"

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
    current_directory = Path.cwd()
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

    process.stdout.close()
    return process.wait(
        timeout=10
    )  # Should already have finished because we have drained stdout


def load_yaml(config_filename: Path):
    """
    Return yaml dict containing config loaded from config_filename.
    """
    with open(config_filename) as f:
        config = yaml.load(f.read())

    return config


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


# https://github.com/minrk/escapism/blob/master/escapism.py
def escape_string(
    to_escape,
    safe=set(string.ascii_letters + string.digits),
    escape_char="_",
    allow_collisions=False,
):
    """Escape a string so that it only contains characters in a safe set.

    Characters outside the safe list will be escaped with _%x_,
    where %x is the hex value of the character.

    If `allow_collisions` is True, occurrences of `escape_char`
    in the input will not be escaped.

    In this case, `unescape` cannot be used to reverse the transform
    because occurrences of the escape char in the resulting string are ambiguous.
    Only use this mode when:

    1. collisions cannot occur or do not matter, and
    2. unescape will never be called.

    .. versionadded: 1.0
        allow_collisions argument.
        Prior to 1.0, behavior was the same as allow_collisions=False (default).

    """
    if sys.version_info >= (3,):

        def _ord(byte):
            return byte

        def _bchr(n):
            return bytes([n])

    else:
        _ord = ord
        _bchr = chr

    def _escape_char(c, escape_char):
        """Escape a single character"""
        buf = []
        for byte in c.encode("utf8"):
            buf.append(escape_char)
            buf.append("%X" % _ord(byte))
        return "".join(buf)

    if isinstance(to_escape, bytes):
        # always work on text
        to_escape = to_escape.decode("utf8")

    if not isinstance(safe, set):
        safe = set(safe)

    if allow_collisions:
        safe.add(escape_char)
    elif escape_char in safe:
        warnings.warn(
            "Escape character %r cannot be a safe character."
            " Set allow_collisions=True if you want to allow ambiguous escaped strings."
            % escape_char,
            RuntimeWarning,
            stacklevel=2,
        )
        safe.remove(escape_char)

    chars = []
    for c in to_escape:
        if c in safe:
            chars.append(c)
        else:
            chars.append(_escape_char(c, escape_char))

    return "".join(chars)


def random_secure_string(
    length: int = 16, chars: str = string.ascii_lowercase + string.digits
):
    return "".join(secrets.choice(chars) for i in range(length))


def set_do_environment():
    os.environ["AWS_ACCESS_KEY_ID"] = os.environ["SPACES_ACCESS_KEY_ID"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ["SPACES_SECRET_ACCESS_KEY"]


def set_docker_image_tag() -> str:
    """Set docker image tag for `jupyterlab`, `jupyterhub`, and `dask-worker`."""
    return os.environ.get("NEBARI_IMAGE_TAG", constants.DEFAULT_NEBARI_IMAGE_TAG)


def set_nebari_dask_version() -> str:
    """Set version of `nebari-dask` meta package."""
    return os.environ.get("NEBARI_DASK_VERSION", constants.DEFAULT_NEBARI_DASK_VERSION)


def get_latest_kubernetes_version(versions: List[str]) -> str:
    return sorted(versions)[-1]


def construct_azure_resource_group_name(
    project_name: str = "",
    namespace: str = "",
    base_resource_group_name: str = "",
    suffix: str = "",
) -> str:
    """
    Construct a resource group name for Azure.

    If the base_resource_group_name is provided, it will be used as the base,
    otherwise default to the project_name-namespace.
    """
    if base_resource_group_name:
        return f"{base_resource_group_name}{suffix}"
    return f"{project_name}-{namespace}{suffix}"


def get_k8s_version_prefix(k8s_version: str) -> str:
    """Return the major.minor version of the k8s version string."""

    k8s_version = str(k8s_version)
    # Split the input string by the first decimal point
    parts = k8s_version.split(".", 1)

    if len(parts) == 2:
        # Extract the part before the second decimal point
        before_second_decimal = parts[0] + "." + parts[1].split(".")[0]
        try:
            # Convert the extracted part to a float
            result = float(before_second_decimal)
            return result
        except ValueError:
            # Handle the case where the conversion to float fails
            return None
    else:
        # Handle the case where there is no second decimal point
        return None


def get_provider_config_block_name(provider):
    PROVIDER_CONFIG_NAMES = {
        "aws": "amazon_web_services",
        "azure": "azure",
        "do": "digital_ocean",
        "gcp": "google_cloud_platform",
    }

    if provider in PROVIDER_CONFIG_NAMES.keys():
        return PROVIDER_CONFIG_NAMES[provider]
    else:
        return provider


def check_environment_variables(variables: Set[str], reference: str) -> None:
    """Check that environment variables are set."""
    required_variables = {
        variable: os.environ.get(variable, None) for variable in variables
    }
    missing_variables = {
        variable for variable, value in required_variables.items() if value is None
    }
    if missing_variables:
        raise ValueError(
            f"""Missing the following required environment variables: {required_variables}\n
            Please see the documentation for more information: {reference}"""
        )
