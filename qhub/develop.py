import os
import datetime

from rich.pretty import pprint

from qhub.provider import docker, git, minikube
from qhub import utils, initialize
from qhub.console import console


QHUB_IMAGE_DIRECTORY = "qhub/template/{{ cookiecutter.repo_directory }}/image/"


def list_dockerfile_images(directory):
    dockerfile_paths = []
    image_names = []
    for path in os.listdir(directory):
        if path.startswith('Dockerfile'):
            dockerfile_paths.append(os.path.join(directory, path))
            image_names.append(os.path.splitext(path)[1][1:])
    return dockerfile_paths, image_names


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
    image_tag = git_head_sha

    develop_directory = os.path.join(git_repo_root, ".qhub", "develop")

    console.rule("Starting Minikube Cluster")
    with utils.timer(
            'Creating Minikube cluster',
            'Created Minikube cluster',
            verbose=verbose):
        minikube.start()
        if not minikube.status():
            raise QHubError("Minikube cluster failed to start")

    console.rule("Building Docker Images")
    dockerfile_paths, image_names = list_dockerfile_images(QHUB_IMAGE_DIRECTORY)
    for dockerfile_path, image_name in zip(dockerfile_paths, image_names):
        image = f"{image_name}:{image_tag}"
        with utils.timer(
                f'Building {os.path.basename(dockerfile_path)} image "{image}"',
                f'Built {os.path.basename(dockerfile_path)} image "{image}"',
                verbose=verbose):
            docker.build(dockerfile_path, QHUB_IMAGE_DIRECTORY, image_name, image_tag)

    console.rule("Uploading Docker Image to Minikube cache")
    for image_name in image_names:
        image = f"{image_name}:{image_tag}"
        with utils.timer(
                f'Uploading "{image}" to local Minikube cache',
                f'Upload complete of "{image}" to local Minikube cache',
                verbose=verbose):
            minikube.image_load(image, overwrite=False)

    initialize_configuration(develop_directory)
