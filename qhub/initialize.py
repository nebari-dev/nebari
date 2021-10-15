import os
import re
import string
import random
import secrets
import tempfile
import logging

import bcrypt
import requests

from qhub.provider.oauth.auth0 import create_client
from qhub.provider.cicd import github
from qhub.provider import git
from qhub.provider.cloud import digital_ocean, azure_cloud
from qhub.utils import namestr_regex, qhub_image_tag, check_cloud_credentials

logger = logging.getLogger(__name__)

BASE_CONFIGURATION = {
    "project_name": None,
    "provider": None,
    "domain": None,
    "certificate": {
        "type": "self-signed",
    },
    "security": {
        "authentication": None,
        "users": {
            "example-user": {
                "uid": 1000,
                "primary_group": "admin",
                "secondary_groups": ["users"],
            }
        },
        "groups": {"users": {"gid": 100}, "admin": {"gid": 101}},
    },
    "default_images": {
        "jupyterhub": f"quansight/qhub-jupyterhub:{qhub_image_tag}",
        "jupyterlab": f"quansight/qhub-jupyterlab:{qhub_image_tag}",
        "dask_worker": f"quansight/qhub-dask-worker:{qhub_image_tag}",
        "dask_gateway": f"quansight/qhub-dask-gateway:{qhub_image_tag}",
        "conda_store": f"quansight/qhub-conda-store:{qhub_image_tag}",
    },
    "storage": {"conda_store": "60Gi", "shared_filesystem": "100Gi"},
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
        }
    },
    "monitoring": {
        "enabled": True,
    },
    "cdsdashboards": {
        "enabled": True,
        "cds_hide_user_named_servers": True,
        "cds_hide_user_dashboard_servers": False,
    },
}

CICD_CONFIGURATION = {"type": "PLACEHOLDER", "branch": "main"}

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

DIGITAL_OCEAN = {
    "region": "nyc3",
    "kubernetes_version": "PLACEHOLDER",
    "node_groups": {
        "general": {"instance": "g-4vcpu-16gb", "min_nodes": 1, "max_nodes": 1},
        "user": {"instance": "g-2vcpu-8gb", "min_nodes": 1, "max_nodes": 5},
        "worker": {"instance": "g-2vcpu-8gb", "min_nodes": 1, "max_nodes": 5},
    },
}
# Digital Ocean image slugs are listed here https://slugs.do-api.dev/

GOOGLE_PLATFORM = {
    "project": "PLACEHOLDER",
    "region": "us-central1",
    "kubernetes_version": "1.18.16-gke.502",
    "node_groups": {
        "general": {"instance": "n1-standard-4", "min_nodes": 1, "max_nodes": 1},
        "user": {"instance": "n1-standard-2", "min_nodes": 1, "max_nodes": 5},
        "worker": {"instance": "n1-standard-2", "min_nodes": 1, "max_nodes": 5},
    },
}

AZURE = {
    "project": "PLACEHOLDER",
    "region": "Central US",
    "kubernetes_version": "PLACEHOLDER",
    "node_groups": {
        "general": {
            "instance": "Standard_D4_v3",
            "min_nodes": 1,
            "max_nodes": 1,
        },
        "user": {"instance": "Standard_D2_v2", "min_nodes": 0, "max_nodes": 5},
        "worker": {
            "instance": "Standard_D2_v2",
            "min_nodes": 1,
            "max_nodes": 5,
        },
    },
    "storage_account_postfix": "".join(
        random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=8)
    ),
}

AMAZON_WEB_SERVICES = {
    "region": "us-west-2",
    "kubernetes_version": "1.18",
    "node_groups": {
        "general": {"instance": "m5.xlarge", "min_nodes": 1, "max_nodes": 1},
        "user": {"instance": "m5.large", "min_nodes": 1, "max_nodes": 5},
        "worker": {"instance": "m5.large", "min_nodes": 1, "max_nodes": 5},
    },
}

DEFAULT_PROFILES = {
    "jupyterlab": [
        {
            "display_name": "Small Instance",
            "description": "Stable environment with 1 cpu / 4 GB ram",
            "default": True,
            "kubespawner_override": {
                "cpu_limit": 1,
                "cpu_guarantee": 0.75,
                "mem_limit": "4G",
                "mem_guarantee": "2.5G",
                "image": f"quansight/qhub-jupyterlab:{qhub_image_tag}",
            },
        },
        {
            "display_name": "Medium Instance",
            "description": "Stable environment with 2 cpu / 8 GB ram",
            "kubespawner_override": {
                "cpu_limit": 2,
                "cpu_guarantee": 1.5,
                "mem_limit": "8G",
                "mem_guarantee": "5G",
                "image": f"quansight/qhub-jupyterlab:{qhub_image_tag}",
            },
        },
    ],
    "dask_worker": {
        "Small Worker": {
            "worker_cores_limit": 1,
            "worker_cores": 0.75,
            "worker_memory_limit": "4G",
            "worker_memory": "2.5G",
            "worker_threads": 1,
            "image": f"quansight/qhub-dask-worker:{qhub_image_tag}",
        },
        "Medium Worker": {
            "worker_cores_limit": 2,
            "worker_cores": 1.5,
            "worker_memory_limit": "8G",
            "worker_memory": "5G",
            "worker_threads": 2,
            "image": f"quansight/qhub-dask-worker:{qhub_image_tag}",
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
            "ipywidgets",
            "qhub-dask ==0.3.13",
            "python-graphviz",
            "numpy",
            "numba",
            "pandas",
        ],
    },
    "environment-dashboard.yaml": {
        "name": "dashboard",
        "channels": ["conda-forge"],
        "dependencies": [
            "python==3.9.7",
            "ipykernel==6.4.1",
            "ipywidgets==7.6.5",
            "qhub-dask==0.3.13",
            "param==1.11.1",
            "python-graphviz==0.17",
            "matplotlib==3.4.3",
            "panel==0.12.4",
            "voila==0.2.16",
            "streamlit==1.0.0",
            "dash==2.0.0",
            "cdsdashboards-singleuser==0.5.7",
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
):
    config = BASE_CONFIGURATION
    config["provider"] = cloud_provider

    if ci_provider is not None and ci_provider != "none":
        config["ci_cd"] = {"type": ci_provider, "branch": "main"}

    if terraform_state is not None:
        config["terraform_state"] = {"type": terraform_state}

    config["theme"]["jupyterhub"]["hub_title"] = f"QHub - { project_name }"
    config["theme"]["jupyterhub"][
        "welcome"
    ] = f"""Welcome to { qhub_domain }. It is maintained by <a href="http://quansight.com">Quansight staff</a>. The hub's configuration is stored in a github repository based on <a href="https://github.com/Quansight/qhub/">https://github.com/Quansight/qhub/</a>. To provide feedback and report any technical problems, please use the <a href="https://github.com/Quansight/qhub/issues">github issue tracker</a>."""

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
    oauth_callback_url = f"https://{qhub_domain}/hub/oauth_callback"

    if auth_provider == "github":
        config["security"]["authentication"] = AUTH_OAUTH_GITHUB
        print(
            "Visit https://github.com/settings/developers and create oauth application"
        )
        print(f"  set the homepage to: https://{qhub_domain}/")
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

        # Generate default password for qhub-init
        default_password = "".join(
            secrets.choice(string.ascii_letters + string.digits) for i in range(16)
        )
        config["security"]["users"]["example-user"]["password"] = bcrypt.hashpw(
            default_password.encode("utf-8"), bcrypt.gensalt()
        ).decode()

        default_password_filename = os.path.join(
            tempfile.gettempdir(), "QHUB_DEFAULT_PASSWORD"
        )
        with open(default_password_filename, "w") as f:
            f.write(default_password)
        os.chmod(default_password_filename, 0o700)

        print(
            f"Securely generated default random password={default_password} for example-user stored at path={default_password_filename}"
        )

    if cloud_provider == "do":
        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = "Autoscaling Compute Environment on Digital Ocean"
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
        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = "Autoscaling Compute Environment on Google Cloud Platform"
        config["google_cloud_platform"] = GOOGLE_PLATFORM
        if kubernetes_version:
            config["google_cloud_platform"]["kubernetes_version"] = kubernetes_version

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
        config["azure"] = AZURE

        if kubernetes_version:
            config["azure"]["kubernetes_version"] = kubernetes_version
        else:
            # first kubernetes version returned by azure sdk is
            # the newest version of kubernetes supported this field needs
            # to be dynamically filled since azure updates the
            # versions so frequently
            config["azure"]["kubernetes_version"] = azure_cloud.kubernetes_versions(
                config["azure"]["region"]
            )[0]

    elif cloud_provider == "aws":
        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = "Autoscaling Compute Environment on Amazon Web Services"
        config["amazon_web_services"] = AMAZON_WEB_SERVICES
        if kubernetes_version:
            config["amazon_web_services"]["kubernetes_version"] = kubernetes_version
    elif cloud_provider == "local":
        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = "Autoscaling Compute Environment"
        config["local"] = LOCAL

    config["profiles"] = DEFAULT_PROFILES
    config["environments"] = DEFAULT_ENVIRONMENTS

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
