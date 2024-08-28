import hashlib
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
        output_base_dir=output_directory,
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
        for filename in sorted(set(map(str, new))):
            table.add_row(str(filename), style="green")
        print(table)
    if updated:
        table = Table("The following files will be updated:", style="deep_sky_blue1")
        for filename in sorted(set(map(str, updated))):
            table.add_row(str(filename), style="green")
        print(table)
    if deleted:
        table = Table("The following files will be deleted:", style="deep_sky_blue1")
        for filename in sorted(set(map(str, deleted))):
            table.add_row(str(filename), style="green")
        print(table)
    if untracked:
        table = Table(
            "The following files are untracked (only exist in output directory):",
            style="deep_sky_blue1",
        )
        for filename in sorted(set(map(str, updated))):
            table.add_row(str(filename), style="green")
        print(table)

    if dry_run:
        print("dry-run enabled no files will be created, updated, or deleted")
    else:
        for filename in new | updated:
            output_filename = output_directory / filename
            output_filename.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(contents[filename], str):
                with open(output_filename, "w") as f:
                    f.write(contents[filename])
            else:
                with open(output_filename, "wb") as f:
                    f.write(contents[filename])

        for path in deleted:
            abs_path = (output_directory / path).resolve()

            if not abs_path.is_relative_to(output_directory):
                raise Exception(
                    f"[ERROR] SHOULD NOT HAPPEN filename was about to be deleted but path={abs_path} is outside of output_directory"
                )

            if abs_path.is_file():
                abs_path.unlink()
            elif abs_path.is_dir():
                shutil.rmtree(abs_path)


def inspect_files(
    output_base_dir: pathlib.Path,
    ignore_filenames: List[str] = None,
    ignore_directories: List[str] = None,
    deleted_paths: List[pathlib.Path] = None,
    contents: Dict[str, str] = None,
):
    """Return created, updated and untracked files by computing a checksum over the provided directory.

    Args:
        output_base_dir (str): Relative base path to output directory
        ignore_filenames (list[str]): Filenames to ignore while comparing for changes
        ignore_directories (list[str]): Directories to ignore while comparing for changes
        deleted_paths (list[Path]): Paths that if exist in output directory should be deleted
        contents (dict): filename to content mapping for dynamically generated files
    """
    ignore_filenames = ignore_filenames or []
    ignore_directories = ignore_directories or []
    contents = contents or {}

    source_files = {}
    output_files = {}

    def list_files(
        directory: pathlib.Path,
        ignore_filenames: List[str],
        ignore_directories: List[str],
    ):
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            yield path

    for filename in contents:
        if isinstance(contents[filename], str):
            source_files[filename] = hashlib.sha256(
                contents[filename].encode("utf8")
            ).hexdigest()
        else:
            source_files[filename] = hashlib.sha256(contents[filename]).hexdigest()

        output_filename = pathlib.Path(output_base_dir) / filename
        if output_filename.is_file():
            output_files[filename] = hash_file(filename)

    deleted_files = set()
    for path in deleted_paths:
        absolute_path = output_base_dir / path
        if absolute_path.exists():
            deleted_files.add(path)

    for filename in list_files(output_base_dir, ignore_filenames, ignore_directories):
        relative_path = pathlib.Path.relative_to(
            pathlib.Path(filename), output_base_dir
        )
        if filename.is_file():
            output_files[relative_path] = hash_file(filename)

    new_files = source_files.keys() - output_files.keys()
    untracted_files = output_files.keys() - source_files.keys()

    updated_files = set()
    for prevalent_file in source_files.keys() & output_files.keys():
        if source_files[prevalent_file] != output_files[prevalent_file]:
            updated_files.add(prevalent_file)

    return new_files, untracted_files, updated_files, deleted_files


def hash_file(file_path: str):
    """Get the hex digest of the given file.

    Args:
        file_path (str): path to file
    """
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
