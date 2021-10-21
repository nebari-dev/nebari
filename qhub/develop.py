import os
import logging

from rich.console import Console

from qhub.provider import docker, git, minikube
from qhub import utils


logger = logging.getLogger(__name__)


console = Console()


QHUB_DOCKERFILE_PATHS = [
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.conda-store',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.dask-gateway',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.dask-worker',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.jupyterhub',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.jupyterlab',
]


def build_dockerfile_image(dockerfile_path, image_tag):
    dockerfile_name = os.path.basename(dockerfile_path)
    build_directory = os.path.dirname(dockerfile_path)
    image_name = os.path.splitext(dockerfile_path)[1][1:]
    image = f"{image_name}:{image_tag}"

    with console.status(f'Building {dockerfile_name} image "{image}"'):
        docker.build(dockerfile_path, build_directory, image_name, image_tag)
    console.print(f'Built {dockerfile_name} image "{image}"')

    return image


def upload_minikube_image(image):
    with console.status(f'Uploading "{image}" to local Minikube cache'):
        minikube.image_load(image, overwrite=False)
    console.print(f'Upload complete of "{image}" to local Minikube cache')


def develop():
    git_repo_root = git.is_git_repo()
    if git_repo_root is None:
        raise utils.QHubError('QHub develop required to run within QHub git repository')

    git_head_sha = git.current_sha()

    for dockerfile_path in QHUB_DOCKERFILE_PATHS:
        image = build_dockerfile_image(dockerfile_path, git_head_sha)
        upload_minikube_image(image)
