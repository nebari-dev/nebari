import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Dict

import pydantic
import requests

from _nebari import constants
from _nebari.provider import git
from _nebari.provider.cicd import github
from _nebari.provider.cloud import (
    amazon_web_services,
    azure_cloud,
    digital_ocean,
    google_cloud,
)
from _nebari.provider.oauth.auth0 import create_client
from _nebari.stages.bootstrap import CiEnum
from _nebari.stages.infrastructure import (
    DEFAULT_AWS_NODE_GROUPS,
    DEFAULT_AZURE_NODE_GROUPS,
    DEFAULT_DO_NODE_GROUPS,
    DEFAULT_GCP_NODE_GROUPS,
    node_groups_to_dict,
)
from _nebari.stages.kubernetes_ingress import CertificateEnum
from _nebari.stages.kubernetes_keycloak import AuthenticationEnum
from _nebari.stages.terraform_state import TerraformStateEnum
from _nebari.utils import get_latest_kubernetes_version, random_secure_string
from _nebari.version import __version__
from nebari.schema import ProviderEnum, github_url_regex

logger = logging.getLogger(__name__)

WELCOME_HEADER_TEXT = "Your open source data science platform, hosted"


def render_config(
    project_name: str,
    nebari_domain: str = None,
    cloud_provider: ProviderEnum = ProviderEnum.local,
    ci_provider: CiEnum = CiEnum.none,
    repository: str = None,
    auth_provider: AuthenticationEnum = AuthenticationEnum.password,
    namespace: str = "dev",
    repository_auto_provision: bool = False,
    auth_auto_provision: bool = False,
    terraform_state: TerraformStateEnum = TerraformStateEnum.remote,
    kubernetes_version: str = None,
    region: str = None,
    disable_prompt: bool = False,
    ssl_cert_email: str = None,
) -> Dict[str, Any]:
    config = {
        "provider": cloud_provider,
        "namespace": namespace,
        "nebari_version": __version__,
    }

    if project_name is None and not disable_prompt:
        project_name = input("Provide project name: ")
    config["project_name"] = project_name

    if nebari_domain is not None:
        config["domain"] = nebari_domain

    config["ci_cd"] = {"type": ci_provider}
    config["terraform_state"] = {"type": terraform_state}

    # Save default password to file
    default_password_filename = Path(tempfile.gettempdir()) / "NEBARI_DEFAULT_PASSWORD"
    config["security"] = {
        "keycloak": {"initial_root_password": random_secure_string(length=32)}
    }
    with default_password_filename.open("w") as f:
        f.write(config["security"]["keycloak"]["initial_root_password"])
    default_password_filename.chmod(0o700)

    config["theme"] = {"jupyterhub": {"hub_title": f"Nebari - { project_name }"}}
    config["theme"]["jupyterhub"][
        "welcome"
    ] = """Welcome! Learn about Nebari's features and configurations in <a href="https://www.nebari.dev/docs/welcome">the documentation</a>. If you have any questions or feedback, reach the team on <a href="https://www.nebari.dev/docs/community#getting-support">Nebari's support forums</a>."""

    config["security"]["authentication"] = {"type": auth_provider}

    if auth_provider == AuthenticationEnum.github:
        config["security"]["authentication"]["config"] = {
            "client_id": os.environ.get(
                "GITHUB_CLIENT_ID",
                "<enter client id or remove to use GITHUB_CLIENT_ID environment variable (preferred)>",
            ),
            "client_secret": os.environ.get(
                "GITHUB_CLIENT_SECRET",
                "<enter client secret or remove to use GITHUB_CLIENT_SECRET environment variable (preferred)>",
            ),
        }
    elif auth_provider == AuthenticationEnum.auth0:
        if auth_auto_provision:
            auth0_config = create_client(config.domain, config.project_name)
            config["security"]["authentication"]["config"] = auth0_config
        else:
            config["security"]["authentication"]["config"] = {
                "client_id": os.environ.get(
                    "AUTH0_CLIENT_ID",
                    "<enter client id or remove to use AUTH0_CLIENT_ID environment variable (preferred)>",
                ),
                "client_secret": os.environ.get(
                    "AUTH0_CLIENT_SECRET",
                    "<enter client secret or remove to use AUTH0_CLIENT_SECRET environment variable (preferred)>",
                ),
                "auth0_subdomain": os.environ.get(
                    "AUTH0_DOMAIN",
                    "<enter subdomain (without .auth0.com) or remove to use AUTH0_DOMAIN environment variable>",
                ),
            }

    if cloud_provider == ProviderEnum.do:
        do_region = region or constants.DO_DEFAULT_REGION
        do_kubernetes_versions = kubernetes_version or get_latest_kubernetes_version(
            digital_ocean.kubernetes_versions()
        )
        config["digital_ocean"] = {
            "kubernetes_version": do_kubernetes_versions,
            "region": do_region,
            "node_groups": node_groups_to_dict(DEFAULT_DO_NODE_GROUPS),
        }

        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = f"{WELCOME_HEADER_TEXT} on Digital Ocean"

    elif cloud_provider == ProviderEnum.gcp:
        gcp_region = region or constants.GCP_DEFAULT_REGION
        gcp_kubernetes_version = kubernetes_version or get_latest_kubernetes_version(
            google_cloud.kubernetes_versions(gcp_region)
        )
        config["google_cloud_platform"] = {
            "kubernetes_version": gcp_kubernetes_version,
            "region": gcp_region,
            "node_groups": node_groups_to_dict(DEFAULT_GCP_NODE_GROUPS),
        }

        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = f"{WELCOME_HEADER_TEXT} on Google Cloud Platform"
        if "PROJECT_ID" in os.environ:
            config["google_cloud_platform"]["project"] = os.environ["PROJECT_ID"]
        elif not disable_prompt:
            config["google_cloud_platform"]["project"] = input(
                "Enter Google Cloud Platform Project ID: "
            )

    elif cloud_provider == ProviderEnum.azure:
        azure_region = region or constants.AZURE_DEFAULT_REGION
        azure_kubernetes_version = kubernetes_version or get_latest_kubernetes_version(
            azure_cloud.kubernetes_versions(azure_region)
        )
        config["azure"] = {
            "kubernetes_version": azure_kubernetes_version,
            "region": azure_region,
            "storage_account_postfix": random_secure_string(length=4),
            "node_groups": node_groups_to_dict(DEFAULT_AZURE_NODE_GROUPS),
        }

        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = f"{WELCOME_HEADER_TEXT} on Azure"

    elif cloud_provider == ProviderEnum.aws:
        aws_region = (
            region
            or os.environ.get("AWS_DEFAULT_REGION")
            or constants.AWS_DEFAULT_REGION
        )
        aws_kubernetes_version = kubernetes_version or get_latest_kubernetes_version(
            amazon_web_services.kubernetes_versions(aws_region)
        )
        config["amazon_web_services"] = {
            "kubernetes_version": aws_kubernetes_version,
            "region": aws_region,
            "node_groups": node_groups_to_dict(DEFAULT_AWS_NODE_GROUPS),
        }
        config["theme"]["jupyterhub"][
            "hub_subtitle"
        ] = f"{WELCOME_HEADER_TEXT} on Amazon Web Services"

    elif cloud_provider == ProviderEnum.existing:
        config["theme"]["jupyterhub"]["hub_subtitle"] = WELCOME_HEADER_TEXT

    elif cloud_provider == ProviderEnum.local:
        config["theme"]["jupyterhub"]["hub_subtitle"] = WELCOME_HEADER_TEXT

    if ssl_cert_email:
        config["certificate"] = {"type": CertificateEnum.letsencrypt.value}
        config["certificate"]["acme_email"] = ssl_cert_email

    # validate configuration and convert to model
    from nebari.plugins import nebari_plugin_manager

    try:
        config_model = nebari_plugin_manager.config_schema.model_validate(config)
    except pydantic.ValidationError as e:
        print(str(e))

    if repository_auto_provision:
        match = re.search(github_url_regex, repository)
        if match:
            git_repository = github_auto_provision(
                config_model, match.group(2), match.group(3)
            )
            git_repository_initialize(git_repository)
        else:
            raise ValueError(
                f"Repository to be auto-provisioned is not the full URL of a GitHub repo: {repository}"
            )

    return config


def github_auto_provision(config: pydantic.BaseModel, owner: str, repo: str):
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
                description=f"Nebari {config.project_name}-{config.provider.value}",
                homepage=f"https://{config.domain}",
            )
        except requests.exceptions.HTTPError as he:
            raise ValueError(
                f"Unable to create GitHub repo https://github.com/{owner}/{repo} - error message from GitHub is: {he}"
            )
    else:
        logger.warning(f"GitHub repo https://github.com/{owner}/{repo} already exists")

    try:
        # Secrets
        if config.provider == ProviderEnum.do:
            for name in {
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "SPACES_ACCESS_KEY_ID",
                "SPACES_SECRET_ACCESS_KEY",
                "DIGITALOCEAN_TOKEN",
            }:
                github.update_secret(owner, repo, name, os.environ[name])
        elif config.provider == ProviderEnum.aws:
            for name in {
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
            }:
                github.update_secret(owner, repo, name, os.environ[name])
        elif config.provider == ProviderEnum.gcp:
            github.update_secret(owner, repo, "PROJECT_ID", os.environ["PROJECT_ID"])
            with open(os.environ["GOOGLE_CREDENTIALS"]) as f:
                github.update_secret(owner, repo, "GOOGLE_CREDENTIALS", f.read())
        elif config.provider == ProviderEnum.azure:
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
    if not git.is_git_repo(Path.cwd()):
        git.initialize_git(Path.cwd())
    git.add_git_remote(git_repository, path=Path.cwd(), remote_name="origin")
