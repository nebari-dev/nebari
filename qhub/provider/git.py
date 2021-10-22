import os
import subprocess
import configparser

from qhub.utils import change_directory, QHubError


class GitError(QHubError):
    pass


def is_git_repo(path : str = None):
    """Determine if given path is a git repo

    Returns the root of the git repository otherwise None if not a git repo
    """
    path = path or os.getcwd()
    root_git_path = os.path.abspath(path)
    while root_git_path != os.sep:
        if ".git" in os.listdir(root_git_path):
            return root_git_path
        root_git_path = os.path.dirname(root_git_path)


def current_sha(path : str = None):
    """Get current commit sha of git directory"""
    path = path or os.getcwd()
    if not is_git_repo(path):
        raise DockerException('cannot get git sha of path that is not git directory')
    with change_directory(path):
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], encoding='utf-8').strip()


def initialize_git(path : str = None):
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
