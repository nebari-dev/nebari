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
        dockerfile_name = image
        build_directory = os.path.dirname(dockerfile_name)
        image_name = os.path.splitext(dockerfile_name)[1][1:]
        logger.info(f'qhub develop build dockerfile={dockerfile_name}')

        with console.status(f'building dockerfile {dockerfile_name} image {image_name}:{image_tag}'):
            import time
            time.sleep(1)
            docker.build(dockerfile_name, build_directory, image_name, image_tag)
        console.print(f"successfully built dockerfile {dockerfile_name} image {image_name}:{image_tag}")


def develop():
    console = Console()

    git_repo_root = git.is_git_repo()
    if git_repo_root is None:
        raise utils.QHubError('QHub develop required to run within QHub git repository')

    git_head_sha = git.current_sha()

    build_docker_images(console, image_tag=git_head_sha)
