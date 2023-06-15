import functools
import hashlib
import os
import pathlib
import shutil
import sys
from typing import Dict, List

from rich import print
from rich.table import Table
from ruamel.yaml import YAML

from _nebari.deprecate import DEPRECATED_FILE_PATHS
from _nebari.stages.base import get_available_stages
from nebari import schema


def render_template(output_directory, config_filename, dry_run=False):
    output_directory = pathlib.Path(output_directory).resolve()

    if output_directory == str(pathlib.Path.home()):
        print("ERROR: Deploying Nebari in home directory is not advised!")
        sys.exit(1)

    # mkdir all the way down to repo dir so we can copy .gitignore
    # into it in remove_existing_renders
    output_directory.mkdir(exist_ok=True, parents=True)

    config_filename = pathlib.Path(config_filename)
    if not config_filename.is_file():
        raise ValueError(
            f"cookiecutter configuration={config_filename} is not filename"
        )

    with config_filename.open() as f:
        yaml = YAML(typ="safe", pure=True)
        config = yaml.load(f)

    # For any config values that start with
    # NEBARI_SECRET_, set the values using the
    # corresponding env var.
    set_env_vars_in_config(config)

    contents = {}
    config = schema.Main.parse_obj(config)
    for stage in get_available_stages():
        contents.update(
            stage(output_directory=output_directory, config=config).render()
        )

    print(contents.keys())

    new, untracked, updated, deleted = inspect_files(
        output_base_dir=str(output_directory),
        ignore_filenames=[
            "terraform.tfstate",
            ".terraform.lock.hcl",
            "terraform.tfstate.backup",
        ],
        ignore_directories=[
            ".terraform",
            "__pycache__",
        ],
        deleted_paths=DEPRECATED_FILE_PATHS,
        contents=contents,
    )

    if new:
        table = Table("The following files will be created:", style="deep_sky_blue1")
        for filename in sorted(new):
            table.add_row(filename, style="green")
        print(table)
    if updated:
        table = Table("The following files will be updated:", style="deep_sky_blue1")
        for filename in sorted(updated):
            table.add_row(filename, style="green")
        print(table)
    if deleted:
        table = Table("The following files will be deleted:", style="deep_sky_blue1")
        for filename in sorted(deleted):
            table.add_row(filename, style="green")
        print(table)
    if untracked:
        table = Table(
            "The following files are untracked (only exist in output directory):",
            style="deep_sky_blue1",
        )
        for filename in sorted(updated):
            table.add_row(filename, style="green")
        print(table)

    if dry_run:
        print("dry-run enabled no files will be created, updated, or deleted")
    else:
        for filename in new | updated:
            output_filename = os.path.join(str(output_directory), filename)
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)

            if isinstance(contents[filename], str):
                with open(output_filename, "w") as f:
                    f.write(contents[filename])
            else:
                with open(output_filename, "wb") as f:
                    f.write(contents[filename])

        for path in deleted:
            abs_path = os.path.abspath(os.path.join(str(output_directory), path))

            # be extra cautious that deleted path is within output_directory
            if not abs_path.startswith(str(output_directory)):
                raise Exception(
                    f"[ERROR] SHOULD NOT HAPPEN filename was about to be deleted but path={abs_path} is outside of output_directory"
                )

            if os.path.isfile(abs_path):
                os.remove(abs_path)
            elif os.path.isdir(abs_path):
                shutil.rmtree(abs_path)


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


def set_env_vars_in_config(config):
    """

    For values in the config starting with 'NEBARI_SECRET_XXX' the environment
    variables are searched for the pattern XXX and the config value is
    modified. This enables setting secret values that should not be directly
    stored in the config file.

    NOTE: variables are most likely written to a file somewhere upon render. In
    order to further reduce risk of exposure of any of these variables you might
    consider preventing storage of the terraform render output.
    """
    private_entries = get_secret_config_entries(config)
    for idx in private_entries:
        set_nebari_secret(config, idx)


def get_secret_config_entries(config, config_idx=None, private_entries=None):
    output = private_entries or []
    if config_idx is None:
        sub_dict = config
        config_idx = []
    else:
        sub_dict = get_sub_config(config, config_idx)

    for key, value in sub_dict.items():
        if type(value) is dict:
            sub_dict_outputs = get_secret_config_entries(
                config, [*config_idx, key], private_entries
            )
            output = [*output, *sub_dict_outputs]
        else:
            if "NEBARI_SECRET_" in str(value):
                output = [*output, [*config_idx, key]]
    return output


def get_sub_config(conf, conf_idx):
    sub_config = functools.reduce(dict.__getitem__, conf_idx, conf)
    return sub_config


def set_sub_config(conf, conf_idx, value):
    get_sub_config(conf, conf_idx[:-1])[conf_idx[-1]] = value


def set_nebari_secret(config, idx):
    placeholder = get_sub_config(config, idx)
    secret_var = get_nebari_secret(placeholder)
    set_sub_config(config, idx, secret_var)


def get_nebari_secret(secret_var):
    env_var = secret_var.lstrip("NEBARI_SECRET_")
    val = os.environ.get(env_var)
    if not val:
        raise EnvironmentError(
            f"Since '{secret_var}' was found in the"
            " Nebari config, the environment variable"
            f" '{env_var}' must be set."
        )
    return val
