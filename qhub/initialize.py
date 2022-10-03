import logging
import os
import random
import re
import secrets
import string
import tempfile

import requests

from qhub.provider import git
from qhub.provider.cicd import github
from qhub.provider.oauth.auth0 import create_client
from qhub.utils import (
    check_cloud_credentials,
    namestr_regex,
    set_docker_image_tag,
    set_kubernetes_version,
    set_qhub_dask_version,
)

from .version import __version__

logger = logging.getLogger(__name__)

qhub_image_tag = set_docker_image_tag()
qhub_dask_version = set_qhub_dask_version()


BASE_CONFIGURATION = {
    "project_name": None,
    "provider": None,
    "domain": None,
    "certificate": {
        "type": "self-signed",
    },
    "security": {
        "authentication": None,
    },
    "default_images": {
        "jupyterhub": f"quay.io/nebari/nebari-jupyterhub:{qhub_image_tag}",
        "jupyterlab": f"quay.io/nebari/nebari-jupyterlab:{qhub_image_tag}",
        "dask_worker": f"quay.io/nebari/nebari-dask-worker:{qhub_image_tag}",
    },
    "storage": {"conda_store": "200Gi", "shared_filesystem": "200Gi"},
    "theme": {
        "jupyterhub": {
            "hub_title": None,
            "hub_subtitle": None,
            "welcome": None,
            "logo": "/hub/custom/images/jupyter_qhub_logo.svg",
            "primary_color": "#4f4173",
            "secondary_color": "#957da6",
            "accent_color": "#32C574",
            "text_color": "#111111",
            "h1_color": "#652e8e",
            "h2_color": "#652e8e",
            "version": f"v{__version__}",
        }
    },
    "helm_extensions": [],
    "monitoring": {
        "enabled": True,
    },
    "argo_workflows": {
        "enabled": True,
    },
    "kbatch": {
        "enabled": True,
    },
    "cdsdashboards": {
        "enabled": True,
        "cds_hide_user_named_servers": True,
        "cds_hide_user_dashboard_servers": False,
    },
}

CICD_CONFIGURATION = {
    "type": "PLACEHOLDER",
    "branch": "main",
    "commit_render": True,
}

AUTH_PASSWORD = {
    "type": "password",
}

AUTH_OAUTH_GITHUB = {
    "type": "GitHub",
    "config": {
        "client_id": "PLACEHOLDER",
        "client_secret": "PLACEHOLDER",
    },
}

AUTH_OAUTH_AUTH0 = {
    "type": "Auth0",
    "config": {
        "client_id": "PLACEHOLDER",
        "client_secret": "PLACEHOLDER",
        "auth0_subdomain": "PLACEHOLDER",
    },
}

LOCAL = {
    "node_selectors": {
        "general": {
            "key": "kubernetes.io/os",
            "value": "linux",
        },
        "user": {
            "key": "kubernetes.io/os",
            "value": "linux",
        },
        "worker": {
            "key": "kubernetes.io/os",
            "value": "linux",
        },
    }
}

EXISTING = {
    "node_selectors": {
        "general": {
            "key": "kubernetes.io/os",
            "value": "linux",
        },
        "user": {
            "key": "kubernetes.io/os",
            "value": "linux",
        },
        "worker": {
            "key": "kubernetes.io/os",
            "value": "linux",
        },
    }
}

DIGITAL_OCEAN = {
    "region": "nyc3",
    "kubernetes_version": "PLACEHOLDER",
    "node_groups": {
        "general": {"instance": "g-8vcpu-32gb", "min_nodes": 1, "max_nodes": 1},
        "user": {"instance": "g-4vcpu-16gb", "min_nodes": 1, "max_nodes": 5},
        "worker": {"instance": "g-4vcpu-16gb", "min_nodes": 1, "max_nodes": 5},
    },
}
# Digital Ocean image slugs are listed here https://slugs.do-api.dev/

GOOGLE_PLATFORM = {
    "project": "PLACEHOLDER",
    "region": "us-central1",
    "kubernetes_version": "PLACEHOLDER",
    "node_groups": {
        "general": {"instance": "n1-standard-8", "min_nodes": 1, "max_nodes": 1},
        "user": {"instance": "n1-standard-4", "min_nodes": 0, "max_nodes": 5},
        "worker": {"instance": "n1-standard-4", "min_nodes": 0, "max_nodes": 5},
    },
}

AZURE = {
    "region": "Central US",
    "kubernetes_version": "PLACEHOLDER",
    "node_groups": {
        "general": {
            "instance": "Standard_D8_v3",
            "min_nodes": 1,
            "max_nodes": 1,
        },
        "user": {"instance": "Standard_D4_v3", "min_nodes": 0, "max_nodes": 5},
        "worker": {
            "instance": "Standard_D4_v3",
            "min_nodes": 0,
            "max_nodes": 5,
        },
    },
    "storage_account_postfix": "".join(
        random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8)
    ),
}

AMAZON_WEB_SERVICES = {
    "region": "us-west-2",
    "kubernetes_version": "PLACEHOLDER",
    "node_groups": {
        "general": {"instance": "m5.2xlarge", "min_nodes": 1, "max_nodes": 1},
        "user": {"instance": "m5.xlarge", "min_nodes": 1, "max_nodes": 5},
        "worker": {"instance": "m5.xlarge", "min_nodes": 1, "max_nodes": 5},
    },
}

DEFAULT_PROFILES = {
    "jupyterlab": [
        {
            "display_name": "Small Instance",
            "description": "Stable environment with 2 cpu / 8 GB ram",
            "default": True,
            "kubespawner_override": {
                "cpu_limit": 2,
                "cpu_guarantee": 1.5,
                "mem_limit": "8G",
                "mem_guarantee": "5G",
            },
        },
        {
            "display_name": "Medium Instance",
            "description": "Stable environment with 4 cpu / 16 GB ram",
            "kubespawner_override": {
                "cpu_limit": 4,
                "cpu_guarantee": 3,
                "mem_limit": "16G",
                "mem_guarantee": "10G",
            },
        },
    ],
    "dask_worker": {
        "Small Worker": {
            "worker_cores_limit": 2,
            "worker_cores": 1.5,
            "worker_memory_limit": "8G",
            "worker_memory": "5G",
            "worker_threads": 2,
        },
        "Medium Worker": {
            "worker_cores_limit": 4,
            "worker_cores": 3,
            "worker_memory_limit": "16G",
            "worker_memory": "10G",
            "worker_threads": 4,
        },
    },
}

DEFAULT_ENVIRONMENTS = {
    "environment-dask.yaml": {
        "name": "dask",
        "channels": ["conda-forge"],
        "dependencies": [
            "python",
            "ipykernel",
            "ipywidgets==7.7.1",
            f"qhub-dask =={qhub_dask_version}",
            "python-graphviz",
            "pyarrow",
            "s3fs",
            "gcsfs",
            "numpy",
            "numba",
            "pandas",
            {
                "pip": [
                    "kbatch",
                ],
            },
        ],
    },
    "environment-dashboard.yaml": {
        "name": "dashboard",
        "channels": ["conda-forge"],
        "dependencies": [
            "python==3.9.13",
            "ipykernel==6.15.1",
            "ipywidgets==7.7.1",
            f"qhub-dask=={qhub_dask_version}",
            "param==1.12.2",
            "python-graphviz==0.20.1",
            "matplotlib==3.3.2",
            "panel==0.13.1",
            "voila==0.3.6",
            "streamlit==1.10.0",
            "dash==2.6.1",
            "cdsdashboards-singleuser==0.6.2",
        ],
    },
}


def render_config(
    project_name,
    qhub_domain,
    cloud_provider,
    ci_provider,
    repository,
    auth_provider,
    namespace=None,
    repository_auto_provision=False,
    auth_auto_provision=False,
    terraform_state=None,
    kubernetes_version=None,
    disable_prompt=False,
    ssl_cert_email=None,
):
    config = BASE_CONFIGURATION.copy()
    config["provider"] = cloud_provider

    if ci_provider is not None and ci_provider != "none":
        config["ci_cd"] = CICD_CONFIGURATION.copy()
        config["ci_cd"]["type"] = ci_provider

    if terraform_state is not None:
        config["terraform_state"] = {"type": terraform_state}

    if project_name is None and not disable_prompt:
        project_name = input("Provide project name: ")
    config["project_name"] = project_name

    if not re.match(namestr_regex, project_name):
        raise ValueError(
            "project name should contain only letters and hyphens/underscores (but not at the start or end)"
        )

    if namespace is not None:
        config["namespace"] = namespace

    if not re.match(namestr_regex, namespace):
        raise ValueError(
            "namespace should contain only letters and hyphens/underscores (but not at the start or end)"
        )

    if qhub_domain is None and not disable_prompt:
        qhub_domain = input("Provide domain: ")
    config["domain"] = qhub_domain

    # In qhub_version only use major.minor.patch version - drop any pre/post/dev suffixes
    config["qhub_version"] = __version__

    # Generate default password for Keycloak root user and also example-user if using password auth
    default_password = "".join(
        secrets.choice(string.ascii_letters + string.digits) for i in range(16)
    )

    # Save default password to file
    default_password_filename = os.path.join(
        tempfile.gettempdir(), "QHUB_DEFAULT_PASSWORD"
    )
    with open(default_password_filename, "w") as f:
        f.write(default_password)
    os.chmod(default_password_filename, 0o700)

    config["theme"]["jupyterhub"]["hub_title"] = f"QHub - { project_name }"
    config["theme"]["jupyterhub"][
        "welcome"
    ] = f"""Welcome to { qhub_domain }. It is maintained by <a href="http://quansight.com">Quansight staff</a>. The hub's configuration is stored in a github repository based on <a href="https://github.com/Quansight/qhub/">https://github.com/Quansight/qhub/</a>. To provide feedback and report any technical problems, please use the <a href="https://github.com/Quansight/qhub/issues">github issue tracker</a>."""

    if auth_provider == "github":
        config["security"]["authentication"] = AUTH_OAUTH_GITHUB.copy()
        if not disable_prompt:
            config["security"]["authentication"]["config"]["client_id"] = input(
                "Github client_id: "
            )
            config["security"]["authentication"]["config"]["client_secret"] = input(
                "Github client_secret: "
            )
    elif auth_provider == "auth0":
        config["security"]["authentication"] = AUTH_OAUTH_AUTH0.copy()

    elif auth_provider == "password":
        config["security"]["authentication"] = AUTH_PASSWORD.copy()

    # Always use default password for keycloak root
    config["security"].setdefault("keycloak", {})[
        "initial_root_password"
    ] = default_password

    if cloud_provider == "do":
        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = "Autoscaling Compute Environment on Digital Ocean"
        config["digital_ocean"] = DIGITAL_OCEAN.copy()
        set_kubernetes_version(config, kubernetes_version, cloud_provider)

    elif cloud_provider == "gcp":
        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = "Autoscaling Compute Environment on Google Cloud Platform"
        config["google_cloud_platform"] = GOOGLE_PLATFORM.copy()
        set_kubernetes_version(config, kubernetes_version, cloud_provider)

        if "PROJECT_ID" in os.environ:
            config["google_cloud_platform"]["project"] = os.environ["PROJECT_ID"]
        elif not disable_prompt:
            config["google_cloud_platform"]["project"] = input(
                "Enter Google Cloud Platform Project ID: "
            )

    elif cloud_provider == "azure":
        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = "Autoscaling Compute Environment on Azure"
        config["azure"] = AZURE.copy()
        set_kubernetes_version(config, kubernetes_version, cloud_provider)

    elif cloud_provider == "aws":
        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = "Autoscaling Compute Environment on Amazon Web Services"
        config["amazon_web_services"] = AMAZON_WEB_SERVICES.copy()
        set_kubernetes_version(config, kubernetes_version, cloud_provider)
        if "AWS_DEFAULT_REGION" in os.environ:
            config["amazon_web_services"]["region"] = os.environ["AWS_DEFAULT_REGION"]

    elif cloud_provider == "existing":
        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = "Autoscaling Compute Environment"
        config["existing"] = EXISTING.copy()

    elif cloud_provider == "local":
        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = "Autoscaling Compute Environment"
        config["local"] = LOCAL.copy()

    config["profiles"] = DEFAULT_PROFILES.copy()
    config["environments"] = DEFAULT_ENVIRONMENTS.copy()

    if ssl_cert_email is not None:
        if not re.match("^[^ @]+@[^ @]+\\.[^ @]+$", ssl_cert_email):
            raise ValueError("ssl-cert-email should be a valid email address")
        config["certificate"] = {
            "type": "lets-encrypt",
            "acme_email": ssl_cert_email,
            "acme_server": "https://acme-v02.api.letsencrypt.org/directory",
        }

    if auth_auto_provision:
        if auth_provider == "auth0":
            auth0_auto_provision(config)

    if repository_auto_provision:
        GITHUB_REGEX = "(https://)?github.com/([^/]+)/([^/]+)/?"
        if re.search(GITHUB_REGEX, repository):
            match = re.search(GITHUB_REGEX, repository)
            git_repository = github_auto_provision(
                config, match.group(2), match.group(3)
            )
            git_repository_initialize(git_repository)
        else:
            raise ValueError(
                f"Repository to be auto-provisioned is not the full URL of a GitHub repo: {repository}"
            )

    return config


def github_auto_provision(config, owner, repo):
    check_cloud_credentials(
        config
    )  # We may need env vars such as AWS_ACCESS_KEY_ID depending on provider

    already_exists = True
    try:
        github.get_repository(owner, repo)
    except requests.exceptions.HTTPError:
        # repo not found
        already_exists = False

    if not already_exists:
        try:
            github.create_repository(
                owner,
                repo,
                description=f'QHub {config["project_name"]}-{config["provider"]}',
                homepage=f'https://{config["domain"]}',
            )
        except requests.exceptions.HTTPError as he:
            raise ValueError(
                f"Unable to create GitHub repo https://github.com/{owner}/{repo} - error message from GitHub is: {he}"
            )
    else:
        logger.warn(f"GitHub repo https://github.com/{owner}/{repo} already exists")

    try:
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
            }:
                github.update_secret(owner, repo, name, os.environ[name])
        elif config["provider"] == "gcp":
            github.update_secret(owner, repo, "PROJECT_ID", os.environ["PROJECT_ID"])
            with open(os.environ["GOOGLE_CREDENTIALS"]) as f:
                github.update_secret(owner, repo, "GOOGLE_CREDENTIALS", f.read())
        elif config["provider"] == "azure":
            for name in {
                "ARM_CLIENT_ID",
                "ARM_CLIENT_SECRET",
                "ARM_SUBSCRIPTION_ID",
                "ARM_TENANT_ID",
            }:
                github.update_secret(owner, repo, name, os.environ[name])
        github.update_secret(
            owner, repo, "REPOSITORY_ACCESS_TOKEN", os.environ["GITHUB_TOKEN"]
        )
    except requests.exceptions.HTTPError as he:
        raise ValueError(
            f"Unable to set Secrets on GitHub repo https://github.com/{owner}/{repo} - error message from GitHub is: {he}"
        )

    return f"git@github.com:{owner}/{repo}.git"


def git_repository_initialize(git_repository):
    if not git.is_git_repo("./"):
        git.initialize_git("./")
    git.add_git_remote(git_repository, path="./", remote_name="origin")


def auth0_auto_provision(config):
    auth0_config = create_client(config["domain"], config["project_name"])
    config["security"]["authentication"]["config"]["client_id"] = auth0_config[
        "client_id"
    ]
    config["security"]["authentication"]["config"]["client_secret"] = auth0_config[
        "client_secret"
    ]
    config["security"]["authentication"]["config"]["auth0_subdomain"] = auth0_config[
        "auth0_subdomain"
    ]
