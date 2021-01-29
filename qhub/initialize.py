import os
import re

import requests

from qhub.provider.oauth.auth0 import create_client
from qhub.provider.cicd import github
from qhub.provider import git
from qhub.constants import DEFAULT_TERRAFORM_VERSION
from qhub.provider.cloud import digital_ocean


BASE_CONFIGURATION = {
    "project_name": None,
    "provider": None,
    "ci_cd": None,
    "domain": None,
    "terraform_version": "0.13.15",
    "security": {
        "authentication": None,
        "users": {
            "costrouc": {
                "uid": 1000,
                "primary_group": "users",
                "secondary_groups": ["admin"],
            }
        },
        "groups": {"users": {"gid": 100}, "admin": {"gid": 101}},
    },
    "default_images": {
        "jupyterhub": "quansight/qhub-jupyterhub:1abd4efb8428a9d851b18e89b6f6e5ef94854334",
        "jupyterlab": "quansight/qhub-jupyterlab:1abd4efb8428a9d851b18e89b6f6e5ef94854334",
        "dask_worker": "quansight/qhub-dask-worker:1abd4efb8428a9d851b18e89b6f6e5ef94854334",
    },
    "storage": {
        "conda_store": "20Gi",
        "shared_filesystem": "10Gi",
    },
}

AUTH_PASSWORD = {
    "type": "password",
}

AUTH_OAUTH_GITHUB = {
    "type": "GitHub",
    "config": {
        "client_id": "PLACEHOLDER",
        "client_secret": "PLACEHOLDER",
        "oauth_callback_url": "PLACEHOLDER",
    },
}

AUTH_OAUTH_AUTH0 = {
    "type": "Auth0",
    "config": {
        "client_id": "PLACEHOLDER",
        "client_secret": "PLACEHOLDER",
        "oauth_callback_url": "PLACEHOLDER",
        "scope": ["openid", "email", "profile"],
        "auth0_subdomain": "PLACEHOLDER",
    },
}

DIGITAL_OCEAN = {
    "region": "nyc3",
    "kubernetes_version": "PLACEHOLDER",
    "node_groups": {
        "general": {"instance": "s-2vcpu-4gb", "min_nodes": 1, "max_nodes": 1},
        "user": {"instance": "s-2vcpu-4gb", "min_nodes": 1, "max_nodes": 4},
        "worker": {
            "instance": "s-2vcpu-4gb",
            "min_nodes": 1,
            "max_nodes": 4,
        },
    },
}

GOOGLE_PLATFORM = {
    "project": "PLACEHOLDER",
    "region": "us-central1",
    "zone": "us-central1-c",
    "availability_zones": ["us-central1-c"],
    "kubernetes_version": "1.14.10-gke.31",
    "node_groups": {
        "general": {
            "instance": "n1-standard-2",
            "min_nodes": 1,
            "max_nodes": 1,
        },
        "user": {"instance": "n1-standard-2", "min_nodes": 1, "max_nodes": 4},
        "worker": {
            "instance": "n1-standard-2",
            "min_nodes": 1,
            "max_nodes": 4,
        },
    },
}

AMAZON_WEB_SERVICES = {
    "region": "us-west-2",
    "availability_zones": ["us-west-2a", "us-west-2b"],
    "kubernetes_version": "1.14",
    "node_groups": {
        "general": {
            "instance": "m5.large",
            "min_nodes": 1,
            "max_nodes": 1,
        },
        "user": {
            "instance": "m5.large",
            "min_nodes": 1,
            "max_nodes": 2,
        },
        "worker": {
            "instance": "m5.large",
            "min_nodes": 1,
            "max_nodes": 2,
        },
    },
}

DEFAULT_PROFILES = {
    "jupyterlab": [
        {
            "display_name": "Small Instance",
            "description": "Stable environment with 1 cpu / 1 GB ram",
            "default": True,
            "kubespawner_override": {
                "cpu_limit": 1,
                "cpu_guarantee": 1,
                "mem_limit": "1G",
                "mem_guarantee": "1G",
                "image": "quansight/qhub-jupyterlab:1abd4efb8428a9d851b18e89b6f6e5ef94854334",
            },
        },
        {
            "display_name": "Medium Instance",
            "description": "Stable environment with 1.5 cpu / 2 GB ram",
            "kubespawner_override": {
                "cpu_limit": 1.5,
                "cpu_guarantee": 1.25,
                "mem_limit": "2G",
                "mem_guarantee": "2G",
                "image": "quansight/qhub-jupyterlab:1abd4efb8428a9d851b18e89b6f6e5ef94854334",
            },
        },
    ],
    "dask_worker": {
        "Small Worker": {
            "worker_cores_limit": 1,
            "worker_cores": 1,
            "worker_memory_limit": "1G",
            "worker_memory": "1G",
            "image": "quansight/qhub-dask-worker:1abd4efb8428a9d851b18e89b6f6e5ef94854334",
        },
        "Medium Worker": {
            "worker_cores_limit": 1.5,
            "worker_cores": 1.25,
            "worker_memory_limit": "2G",
            "worker_memory": "2G",
            "image": "quansight/qhub-dask-worker:1abd4efb8428a9d851b18e89b6f6e5ef94854334",
        },
    },
}

DEFAULT_ENVIRONMENTS = {
    "environment-default.yaml": {
        "name": "default",
        "channels": ["conda-forge", "defaults"],
        "dependencies": [
            "python=3.8",
            "ipykernel",
            "ipywidgets",
            "dask==2.14.0",
            "distributed==2.14",
            "dask-gateway=0.6.1",
            "numpy",
            "numba",
            "pandas",
        ],
    }
}


def render_config(
    project_name,
    qhub_domain,
    cloud_provider,
    ci_provider,
    repository,
    auth_provider,
    repository_auto_provision=False,
    auth_auto_provision=False,
    terraform_version=DEFAULT_TERRAFORM_VERSION,
    kubernetes_version=None,
    disable_prompt=False,
):
    config = BASE_CONFIGURATION
    config["provider"] = cloud_provider
    config["ci_cd"] = ci_provider

    config["terraform_version"] = terraform_version

    if project_name is None and not disable_prompt:
        project_name = input("Provide project name: ")
    config["project_name"] = project_name

    if qhub_domain is None and not disable_prompt:
        qhub_domain = input("Provide domain jupyter.<domain name>: ")
    config["domain"] = qhub_domain
    oauth_callback_url = f"https://jupyter.{qhub_domain}/hub/oauth_callback"

    if auth_provider == "github":
        config["security"]["authentication"] = AUTH_OAUTH_GITHUB
        print(
            "Visit https://github.com/settings/developers and create oauth application"
        )
        print(f"  set the homepage to: https://jupyter.{qhub_domain}/")
        print(f"  set the callback_url to: {oauth_callback_url}")
        if not disable_prompt:
            config["security"]["authentication"]["config"]["client_id"] = input(
                "Github client_id: "
            )
            config["security"]["authentication"]["config"]["client_secret"] = input(
                "Github client_secret: "
            )
            config["security"]["authentication"]["config"][
                "oauth_callback_url"
            ] = oauth_callback_url
    elif auth_provider == "auth0":
        config["security"]["authentication"] = AUTH_OAUTH_AUTH0
        config["security"]["authentication"]["config"][
            "oauth_callback_url"
        ] = oauth_callback_url
    elif auth_provider == "password":
        config["security"]["authentication"] = AUTH_PASSWORD

    if cloud_provider == "do":
        config["digital_ocean"] = DIGITAL_OCEAN
        if kubernetes_version:
            config["digital_ocean"]["kubernetes_version"] = kubernetes_version
        else:
            # first kubernetes version returned by Digital Ocean api is
            # the newest version of kubernetes supported this field needs
            # to be dynamically filled since digital ocean updates the
            # versions so frequently
            config["digital_ocean"][
                "kubernetes_version"
            ] = digital_ocean.kubernetes_versions()[0]["slug"]
    elif cloud_provider == "gcp":
        config["google_cloud_platform"] = GOOGLE_PLATFORM
        if kubernetes_version:
            config["google_cloud_platform"]["kubernetes_version"] = kubernetes_version

        if "PROJECT_ID" in os.environ:
            config["google_cloud_platform"]["project"] = os.environ["PROJECT_ID"]
        elif not disable_prompt:
            config["google_cloud_platform"]["project"] = input(
                "Enter Google Cloud Platform Project ID: "
            )
    elif cloud_provider == "aws":
        config["amazon_web_services"] = AMAZON_WEB_SERVICES
        if kubernetes_version:
            config["amazon_web_services"]["kubernetes_version"] = kubernetes_version

    config["profiles"] = DEFAULT_PROFILES
    config["environments"] = DEFAULT_ENVIRONMENTS

    if auth_auto_provision:
        if auth_provider == "auth0":
            auth0_auto_provision(config)

    if repository_auto_provision:
        GITHUB_REGEX = "github.com/(.*)/(.*)"
        if re.search(GITHUB_REGEX, repository):
            match = re.search(GITHUB_REGEX, repository)
            git_repository = github_auto_provision(
                config, match.group(1), match.group(2)
            )
            git_repository_initialize(git_repository)

    return config


def github_auto_provision(config, owner, repo):
    try:
        github.get_repository(owner, repo)
    except requests.exceptions.HTTPError:
        # repo not found
        github.create_repository(
            owner,
            repo,
            description=f'QHub {config["project_name"]}-{config["provider"]}',
            homepage='https://jupyter.{config["domain"]}',
        )

    # Secrets
    if config["provider"] == "do":
        for name in {
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "SPACES_ACCESS_KEY_ID",
            "SPACES_SECRET_ACCESS_KEY",
            "DIGITALOCEAN_TOKEN",
        }:
            github.update_secret(owner, repo, name, os.environ[name])
    elif config["provider"] == "aws":
        for name in {
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_DEFAULT_REGION",
        }:
            github.update_secret(owner, repo, name, os.environ[name])
    elif config["provider"] == "gcp":
        github.update_secret(owner, repo, "PROJECT_ID", os.environ["PROJECT_ID"])
        with open(os.environ["GOOGLE_CREDENTIALS"]) as f:
            github.update_secret(owner, repo, "GOOGLE_CREDENTIALS", f.read())

    github.update_secret(
        owner, repo, "REPOSITORY_ACCESS_TOKEN", os.environ["GITHUB_TOKEN"]
    )

    return f"git@github.com:{owner}/{repo}.git"


def git_repository_initialize(git_repository):
    if not git.is_git_repo("./"):
        git.initialize_git("./")
    git.add_git_remote(git_repository, path="./", remote_name="origin")


def auth0_auto_provision(config):
    auth0_config = create_client(f"jupyter.{config['domain']}", config["project_name"])
    config["security"]["authentication"]["config"]["client_id"] = auth0_config[
        "client_id"
    ]
    config["security"]["authentication"]["config"]["client_secret"] = auth0_config[
        "client_secret"
    ]
    config["security"]["authentication"]["config"]["auth0_subdomain"] = auth0_config[
        "auth0_subdomain"
    ]
