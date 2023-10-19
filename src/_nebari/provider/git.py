import configparser
import os
import subprocess
from pathlib import Path
from typing import Optional

from _nebari.utils import change_directory


def is_git_repo(path: Optional[Path] = None):
    path = path or Path.cwd()
    return ".git" in os.listdir(path)


def initialize_git(path: Optional[Path] = None):
    path = path or Path.cwd()
    with change_directory(path):
        subprocess.check_output(["git", "init"])
        # Ensure initial branch is called main
        subprocess.check_output(["git", "checkout", "-b", "main"])


def add_git_remote(
    remote_path: str, path: Optional[Path] = None, remote_name: str = "origin"
):
    path = path or Path.cwd()

    c = configparser.ConfigParser()
    with open(path / ".git/config") as f:
        c.read_file(f)
    if f'remote "{remote_name}"' in c:
        if c[f'remote "{remote_name}"']["url"] == remote_path:
            return  # no action needed
        else:
            raise ValueError(
                f"git add remote would change existing remote name={remote_name}"
            )

    with change_directory(path):
        subprocess.check_output(["git", "remote", "add", remote_name, remote_path])
