from collections import OrderedDict

import click
from cookiecutter import prompt
import yaml

from qhub_ops.provider.cloud import digital_ocean, google_cloud, amazon_web_services


DEFAULT_CONFIGURATION = {
    "repo_name": "qhub-deployment",
    "project_name": "qhub-jupyterhub",
    "providers": {
        "Google Cloud Platform (GCP)": "gcp",
        "Amazon Web Services (AWS)": "aws",
        "Digital Ocean (DO)": "do",
    },
    "ci_cd": {"Github Actions": "github-actions"},
    "authentication": {"Github OAuth": "github"},
    "node_groups": {"general", "user", "worker"},
}


def read_user_multichoice_dict(var_name, options):
    choice_map = OrderedDict(
        ("{}".format(i), value) for i, value in enumerate(list(options.keys()), 1)
    )
    choices = choice_map.keys()
    default = "1"

    choice_lines = ["{} - {}".format(*c) for c in choice_map.items()]
    prompt = "\n".join(
        (
            "Select {}:".format(var_name),
            "\n".join(choice_lines),
            "Choose from {}".format(", ".join(choices)),
        )
    )

    user_choice = click.prompt(prompt, type=str, default=default, show_choices=False)
    return [options[choice_map[_.strip()]] for _ in user_choice.split(",")]


def prompt_list(var_name):
    return click.prompt(f'{var_name} ("," delimited)').split(",")


def prompt_dict(message, d, sort=True):
    options = list(d.keys())
    if sort:
        options = sorted(options)

    return d[prompt.read_user_choice(message, options)]


def prompt_range(message, min_value, max_value, default_value):
    while True:
        value = click.prompt(
            f"Select {message} [{min_value} - {max_value}]",
            type=int,
            default=default_value,
        )
        if min_value <= value <= max_value:
            break
    return value


def prompt_github_config(config):
    client_id = click.prompt("GitHub Client ID")
    client_secret = click.prompt("GitHub Client Secret")

    config["auth"]["type"] = "custom"
    config["auth"]["github"] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "oauth_callback_url": f'https://{config["endpoint"]}/hub/oauth_callback',
    }


def prompt_auth0_config(config):
    client_id = click.prompt("Auth0 Client ID")
    client_secret = click.prompt("Auth0 Client Secret")
    auth0_subdomain = click.prompt("Auth0 Subdomain")

    config["auth"]["type"] = "custom"
    config["auth"]["custom"] = {
        "className": "oauthenticator.auth0.Auth0OAuthenticator",
        "client_id": client_id,
        "client_secret": client_secret,
        "oauth_callback_url": f'https://{config["endpoint"]}/hub/oauth_callback',
        "scopes": ["openid", "profile", "email"],
    }


def prompt_do_config(config):
    config["digital_ocean"] = {}
    config["digital_ocean"]["region"] = prompt_dict("Region", digital_ocean.regions())
    config["digital_ocean"]["kubernetes_version"] = prompt_dict(
        "Kubernetes Version", digital_ocean.kubernetes_versions()
    )

    config["digital_ocean"]["node_groups"] = {}
    for node_group in DEFAULT_CONFIGURATION["node_groups"]:
        instance_type = prompt_dict(
            f"{node_group} node group instance type", digital_ocean.instances()
        )
        min_nodes = prompt_range(f"{node_group} node group min nodes", 1, 999_999, 1)
        max_nodes = prompt_range(
            f"{node_group} node group min nodes", min_nodes, 999_999, min_nodes
        )

        config["digital_ocean"]["node_groups"][node_group] = {
            "instance": instance_type,
            "min_nodes": min_nodes,
            "max_nodes": max_nodes,
        }


def prompt_gcp_config(config):
    project = prompt_dict("Project", google_cloud.projects())
    config["google_cloud_platform"]["project"] = project
    region = prompt_dict("Region", google_cloud.regions(project))
    config["google_cloud_platform"]["region"] = region
    config["google_cloud_platform"]["zone"] = prompt_dict(
        "Zone", google_cloud.zones(project, region)
    )
    availability_zones = read_user_multichoice_dict(
        "Availability Zone", google_cloud.zones(project, region)
    )
    config["google_cloud_platform"]["availability_zones"] = str(
        availability_zones
    ).replace("'", '"')
    config["google_cloud_platform"]["kubernetes_version"] = prompt_dict(
        "Kubernetes Version", google_cloud.kubernetes_versions(region)
    )

    config["google_cloud_platform"]["node_groups"] = {}
    for node_group in DEFAULT_CONFIGURATION["node_groups"]:
        instance_type = prompt_dict(
            f"{node_group} node group instance type", google_cloud.instances(project),
        )
        min_nodes = prompt_range(f"{node_group} node group min nodes", 0, 999_999, 1)
        max_nodes = prompt_range(
            f"{node_group} node group min nodes", min_nodes, 999_999, min_nodes
        )

        config["google_cloud_platform"]["node_groups"][node_group] = {
            "instance": instance_type,
            "min_nodes": min_nodes,
            "max_nodes": max_nodes,
        }


def prompt_aws_config(config):
    region = prompt_dict("Region", amazon_web_services.regions())
    config["amazon_web_services"]["region"] = region
    availability_zones = read_user_multichoice_dict(
        "Availability Zones", amazon_web_services.zones(project, region)
    )
    config["amazon_web_services"]["availability_zones"] = str(
        availability_zones
    ).replace("'", '"')
    config["amazon_web_services"]["kubernetes_version"] = prompt_dict(
        "Kubernetes Version", amazon_web_services.kubernetes_versions()
    )

    config["amazon_web_services"]["node_groups"] = {}
    for node_group in DEFAULT_CONFIGURATION["node_groups"]:
        instance_type = prompt_dict(
            f"{node_group} node group instance type",
            amazon_web_services.instances(region),
        )
        min_nodes = prompt_range(f"{node_group} node group min nodes", 0, 999_999, 1)
        max_nodes = prompt_range(
            f"{node_group} node group min nodes", min_nodes, 999_999, min_nodes
        )

        config["amazon_web_services"]["node_groups"][node_group] = {
            "instance": instance_type,
            "min_nodes": min_nodes,
            "max_nodes": max_nodes,
        }


def prompt_config():
    repo_name = prompt.read_user_variable(
        "Repository Name", DEFAULT_CONFIGURATION["repo_name"]
    )
    project_name = prompt.read_user_variable(
        "Project Name", DEFAULT_CONFIGURATION["project_name"]
    )

    ci_cd = prompt_dict("Continuous Delivery", DEFAULT_CONFIGURATION["ci_cd"])

    endpoint = prompt.read_user_variable("Jupyterhub Endpoint")

    authentication = prompt_dict(
        "Authentication", DEFAULT_CONFIGURATION["authentication"]
    )

    provider = prompt_dict("Cloud Provider", DEFAULT_CONFIGURATION["providers"])

    config = {
        "repo_name": repo_name,
        "project_name": project_name,
        "provider": provider,
        "ci_cd": ci_cd,
        "endpoint": endpoint,
    }

    auth_config = {"auth": {"admin": {"access": True, "users": []}, "whitelist": []}}

    if authentication == "github":
        prompt_github_auth_config(auth_config)
    elif authentication == "auth0":
        prompt_auth0_config(auth_config)

    config["authentication"] = yaml.dumps(auth_config)

    if provider == "do":
        prompt_do_config(config)
    elif provider == "gcp":
        prompt_gcp_config(config)
    elif provider == "aws":
        prompt_aws_config(config)
    return config


COOKIECUTTER_CONFIG = prompt_config()
