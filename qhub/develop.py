import os
import datetime

from ruamel import yaml
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


def initialize_configuration(directory, image_tag, verbose=True):
    config_path = os.path.join(directory, 'qhub-config.yaml')

    config = initialize.render_config(
        f'qhubdevelop',
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

    # replace the docker images used in deployment
    config["default_images"] = {
        "jupyterhub": f"docker.io/library/jupyterhub:{image_tag}",
        "jupyterlab": f"docker.io/library/jupyterlab:{image_tag}",
        "dask_worker": f"docker.io/library/dask-worker:{image_tag}",
        "dask_gateway": f"docker.io/library/dask-gateway:{image_tag}",
        "conda_store": f"docker.io/library/conda-store:{image_tag}",
    }

    for jupyterlab_profile in config["profiles"]["jupyterlab"]:
        jupyterlab_profile["kubespawner_override"]["image"] = f"docker.io/library/jupyterlab:{image_tag}"

    for name, dask_worker_profile in config["profiles"]["dask_worker"].items():
        dask_worker_profile["image"] = f"docker.io/library/dask-worker:{image_tag}"

    if verbose:
        pprint(config)

    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config


def develop(verbose=True):
    git_repo_root = git.is_git_repo()
    if git_repo_root is None:
        raise utils.QHubError('QHub develop required to run within QHub git repository')

    git_head_sha = git.current_sha()
    image_tag = git_head_sha

    develop_directory = os.path.join(git_repo_root, ".qhub", "develop")

    console.rule("Starting Minikube cluster")
    with utils.timer(
            'Creating Minikube cluster',
            'Created Minikube cluster',
            verbose=verbose):
        minikube.start()
        if not minikube.status():
            raise QHubError("Minikube cluster failed to start")

    console.rule("Building Docker images")
    dockerfile_paths, image_names = list_dockerfile_images(QHUB_IMAGE_DIRECTORY)
    for dockerfile_path, image_name in zip(dockerfile_paths, image_names):
        image = f"{image_name}:{image_tag}"
        with utils.timer(
                f'Building {os.path.basename(dockerfile_path)} image "{image}"',
                f'Built {os.path.basename(dockerfile_path)} image "{image}"',
                verbose=verbose):
            docker.build(dockerfile_path, QHUB_IMAGE_DIRECTORY, image_name, image_tag)

    console.rule("Uploading Docker image to Minikube cache")
    for image_name in image_names:
        image = f"{image_name}:{image_tag}"
        with utils.timer(
                f'Uploading "{image}" to local Minikube cache',
                f'Upload complete of "{image}" to local Minikube cache',
                verbose=verbose):
            minikube.image_load(image, overwrite=False)

    initialize_configuration(develop_directory, image_tag)
