import os
import logging

from rich.console import Console

from qhub.provider import docker, git
from qhub import utils


logger = logging.getLogger(__name__)


QHUB_IMAGES = [
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.conda-store',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.dask-gateway',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.dask-worker',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.jupyterhub',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.jupyterlab',
]


def build_docker_images(console, image_tag):
    for image in QHUB_IMAGES:
        dockerfile_path = image
        dockerfile_name = os.path.basename(dockerfile_path)
        build_directory = os.path.dirname(dockerfile_path)
        image_name = os.path.splitext(dockerfile_path)[1][1:]

        with console.status(f'Building {dockerfile_name} image "{image_name}:{image_tag}"'):
            docker.build(dockerfile_name, build_directory, image_name, image_tag)
        console.print(f'Built {dockerfile_name} image "{image_name}:{image_tag}"')


def develop():
    console = Console()

    git_repo_root = git.is_git_repo()
    if git_repo_root is None:
        raise utils.QHubError('QHub develop required to run within QHub git repository')

    git_head_sha = git.current_sha()

    build_docker_images(console, image_tag=git_head_sha)
