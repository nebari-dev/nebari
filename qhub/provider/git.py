import os
import subprocess
import configparser

from qhub.utils import change_directory


def is_git_repo(path=None):
    path = path or os.getcwd()
    return ".git" in os.listdir(path)


def initialize_git(path=None):
    path = path or os.getcwd()
    with change_directory(path):
        subprocess.check_output(["git", "init"])
        # Ensure initial branch is called main
        subprocess.check_output(["git", "checkout", "-b", "main"])


def add_git_remote(remote_path, path=None, remote_name="origin"):
    path = path or os.getcwd()

    c = configparser.ConfigParser()
    with open(os.path.join(path, ".git/config")) as f:
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
