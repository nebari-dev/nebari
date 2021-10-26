import os
import datetime

from ruamel import yaml
from rich.pretty import pprint

from qhub.provider import docker, git, minikube
from qhub import utils, initialize, deploy, render
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


def initialize_configuration(directory, image_tag, verbose=True, build_images=True):
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

    if build_images:
        # replace the docker images used in deployment
        config["default_images"] = {
            "jupyterhub": f"jupyterhub:{image_tag}",
            "jupyterlab": f"jupyterlab:{image_tag}",
            "dask_worker": f"dask-worker:{image_tag}",
            "dask_gateway": f"dask-gateway:{image_tag}",
            "conda_store": f"conda-store:{image_tag}",
        }

        for jupyterlab_profile in config["profiles"]["jupyterlab"]:
            jupyterlab_profile["kubespawner_override"]["image"] = f"jupyterlab:{image_tag}"

        for name, dask_worker_profile in config["profiles"]["dask_worker"].items():
            dask_worker_profile["image"] = f"dask-worker:{image_tag}"

    console.print(f"Generated QHub configuration at path={config_path}")

    os.makedirs(directory, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config


def develop(verbose=True, build_images=True, kubernetes_version="v1.20.2"):
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
        minikube.start(kubernetes_version=kubernetes_version)
        if not minikube.status():
            raise QHubError("Minikube cluster failed to start")
        minikube.configure_metallb()
        minikube.addons_enable("metallb")

    if build_images:
        console.rule("Building Docker images")
        dockerfile_paths, image_names = list_dockerfile_images(QHUB_IMAGE_DIRECTORY)
        for dockerfile_path, image_name in zip(dockerfile_paths, image_names):
            image = f"{image_name}:{image_tag}"
            with utils.timer(
                    f'Building {os.path.basename(dockerfile_path)} image "{image}"',
                    f'Built {os.path.basename(dockerfile_path)} image "{image}"',
                    verbose=verbose):
                minikube.image_build(dockerfile_path, QHUB_IMAGE_DIRECTORY, image_name, image_tag)

    console.rule("Installing QHub")
    config = initialize_configuration(develop_directory, image_tag, build_images=build_images)

    with utils.timer(
            f'Rendering qhub-config.yaml terraform files to directory={develop_directory}',
            f'Rendered qhub-config.yaml terraform files to directory={develop_directory}',
            verbose=verbose):
        render.render_template(
            develop_directory,
            os.path.join(develop_directory, "qhub-config.yaml"),
            force=True)

    with utils.change_directory(develop_directory):
        deploy.guided_install(config, dns_provider=None, dns_auto_provision=False, disable_prompt=True, verbose=verbose)

    console.print(
        f'Development documentation https://docs.qhub.dev/en/stable/source/dev_guide/\n'
    )
