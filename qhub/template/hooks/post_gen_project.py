import os
import shutil

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)
CI_PROVIDER = "{{ cookiecutter.ci_cd.type | default('none') }}"


def remove_directory(dirpath):
    shutil.rmtree(os.path.join(PROJECT_DIRECTORY, dirpath))


def remove_file(filepath):
    os.remove(os.path.join(PROJECT_DIRECTORY, filepath))


if __name__ == "__main__":
    # Remove any unused CI
    if CI_PROVIDER != "github-actions":
        remove_directory(".github")

    if CI_PROVIDER != "gitlab-ci":
        remove_file(".gitlab-ci.yml")
