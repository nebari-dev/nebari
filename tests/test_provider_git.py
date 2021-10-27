import tempfile
import os

from qhub.provider import git


def test_empty_directory():
    with tempfile.TemporaryDirectory() as tempdir:
        assert git.is_git_repo(tempdir) is None


def test_fake_git_directory():
    with tempfile.TemporaryDirectory() as tempdir:
        os.makedirs(os.path.join(tempdir, ".git"))
        assert git.is_git_repo(tempdir) == tempdir


def test_create_git_repo():
    with tempfile.TemporaryDirectory() as tempdir:
        git.initialize_git(tempdir)
        assert git.is_git_repo(tempdir) == tempdir
