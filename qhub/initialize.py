import os

from qhub.provider.oauth.auth0 import create_client


BASE_CONFIGURATION = {
    "project_name": None,
    "provider": None,
    "ci_cd": None,
    "domain": None,
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

OAUTH_GITHUB = {
    "type": "GitHub",
    "config": {
        "client_id": "PLACEHOLDER",
        "client_secret": "PLACEHOLDER",
        "oauth_callback_url": "PLACEHOLDER",
    },
}

OAUTH_AUTH0 = {
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
    "kubernetes_version": "1.18.8-do.0",
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
    oauth_provider,
    oauth_auto_provision,
):
    config = BASE_CONFIGURATION
    config["provider"] = cloud_provider
    config["ci_cd"] = ci_provider

    if project_name is None:
        project_name = input("Provide project name: ")
    config["project_name"] = project_name

    if qhub_domain is None:
        qhub_domain = input("Provide domain jupyter.<domain name>: ")
    config["domain"] = qhub_domain
    oauth_callback_url = f"https://jupyter.{qhub_domain}/hub/oauth_callback"

    if oauth_provider == "github":
        config["security"]["authentication"] = OAUTH_GITHUB
        print(
            "Visit https://github.com/settings/developers and create oauth application"
        )
        print(f"  set the homepage to: https://jupyter.{qhub_domain}/")
        print(f"  set the callback_url to: {oauth_callback_url}")
        config["security"]["authentication"]["config"]["client_id"] = input(
            "Github client_id: "
        )
        config["security"]["authentication"]["config"]["client_id"] = input(
            "Github client_secret: "
        )
        config["security"]["authentication"]["config"][
            "oauth_callback_url"
        ] = oauth_callback_url
    elif oauth_provider == "auth0":
        config["security"]["authentication"] = OAUTH_AUTH0
        config["security"]["authentication"]["config"][
            "oauth_callback_url"
        ] = oauth_callback_url

    if cloud_provider == "do":
        config["digital_ocean"] = DIGITAL_OCEAN
    elif cloud_provider == "gcp":
        config["google_cloud_platform"] = GOOGLE_PLATFORM
        if "PROJECT_ID" in os.environ:
            config["google_cloud_platform"]["project"] = os.environ["PROJECT_ID"]
        else:
            config["google_cloud_platform"]["project"] = input(
                "Enter Google Cloud Platform Project ID: "
            )
    elif cloud_provider == "aws":
        config["amazon_web_services"] = AMAZON_WEB_SERVICES

    config["profiles"] = DEFAULT_PROFILES
    config["environments"] = DEFAULT_ENVIRONMENTS

    if oauth_auto_provision:
        if oauth_provider == "auth0":
            auth0_auto_provision(config)

    return config


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
