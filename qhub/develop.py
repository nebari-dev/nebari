import os
import datetime

from rich.pretty import pprint

from qhub.provider import docker, git, minikube
from qhub import utils, initialize


QHUB_DOCKERFILE_PATHS = [
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.conda-store',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.dask-gateway',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.dask-worker',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.jupyterhub',
    'qhub/template/{{ cookiecutter.repo_directory }}/image/Dockerfile.jupyterlab',
]


def start_minikube_cluster():

def build_dockerfile_image(dockerfile_path, image_tag):
    dockerfile_name = os.path.basename(dockerfile_path)
    build_directory = os.path.dirname(dockerfile_path)
    image_name = os.path.splitext(dockerfile_path)[1][1:]
    image = f"{image_name}:{image_tag}"

    with utils.timer(
            f'Building {dockerfile_name} image "{image}"',
            f'Built {dockerfile_name} image "{image}"'):
        docker.build(dockerfile_path, build_directory, image_name, image_tag)

    return image


def upload_minikube_image(image):
    with utils.timer(
            f'Uploading "{image}" to local Minikube cache',
            f'Upload complete of "{image}" to local Minikube cache'):
        minikube.image_load(image, overwrite=False)


def initialize_configuration(directory):
    config_path = os.path.join(directory, 'qhub-config.yaml')
    config = initialize.render_config(
        f'local-{datetime.datetime.utcnow().strftime("%Y%m%d-%H%M")}',
        qhub_domain='github-actions.qhub.dev',
        cloud_provider='local',
        ci_provider='none',
        repository=None,
        auth_provider='password',
        namespace='dev',
        repository_auto_provision=False,
        auth_auto_provision=False,
        terraform_state=None,
        disable_prompt=True
    )
    pprint(config)


def develop(verbose=True):
    git_repo_root = git.is_git_repo()
    if git_repo_root is None:
        raise utils.QHubError('QHub develop required to run within QHub git repository')

    git_head_sha = git.current_sha()

    develop_directory = os.path.join(git_repo_root, ".qhub", "develop")

    console.rule("Starting Minikube Cluster")
    with utils.timer(
            'Creating Minikube cluster',
            'Created Minikube cluster',
            verbose=verbose):
        minikube.start()

    for dockerfile_path in QHUB_DOCKERFILE_PATHS:
        image = build_dockerfile_image(dockerfile_path, git_head_sha)
        upload_minikube_image(image)

    initialize_configuration(develop_directory)
