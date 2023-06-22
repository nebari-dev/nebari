import hashlib
import os
import pathlib
import shutil
import sys
from typing import Dict, List

from rich import print
from rich.table import Table

from _nebari.deprecate import DEPRECATED_FILE_PATHS
from nebari import hookspecs, schema


def render_template(
    output_directory: pathlib.Path,
    config: schema.Main,
    stages: List[hookspecs.NebariStage],
    dry_run=False,
):
    output_directory = pathlib.Path(output_directory).resolve()
    if output_directory == pathlib.Path.home():
        print("ERROR: Deploying Nebari in home directory is not advised!")
        sys.exit(1)

    # mkdir all the way down to repo dir so we can copy .gitignore
    # into it in remove_existing_renders
    output_directory.mkdir(exist_ok=True, parents=True)

    contents = {}
    for stage in stages:
        contents.update(
            stage(output_directory=output_directory, config=config).render()
        )

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
