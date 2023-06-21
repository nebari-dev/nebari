import logging
import os
import re
import tempfile

import requests

from _nebari.provider import git
from _nebari.provider.cicd import github
from _nebari.provider.oauth.auth0 import create_client
from _nebari.utils import check_cloud_credentials
from _nebari.version import __version__
from nebari import schema
from nebari.plugins import extend_schema

logger = logging.getLogger(__name__)

WELCOME_HEADER_TEXT = "Your open source data science platform, hosted"


def render_config(
    project_name: str,
    nebari_domain: str,
    cloud_provider: schema.ProviderEnum = schema.ProviderEnum.local,
    ci_provider: schema.CiEnum = schema.CiEnum.none,
    repository: str = None,
    auth_provider: schema.AuthenticationEnum = schema.AuthenticationEnum.password,
    namespace: str = "dev",
    repository_auto_provision: bool = False,
    auth_auto_provision: bool = False,
    terraform_state: schema.TerraformStateEnum = schema.TerraformStateEnum.remote,
    kubernetes_version: str = None,
    disable_prompt: bool = False,
    ssl_cert_email: str = None,
):
    if project_name is None and not disable_prompt:
        project_name = input("Provide project name: ")

    if nebari_domain is None and not disable_prompt:
        nebari_domain = input("Provide domain: ")

    # extend schema with plugin specific schemas
    Main = extend_schema(schema.Main)

    config = Main(
        project_name=project_name,
        domain=nebari_domain,
        provider=cloud_provider,
        namespace=namespace,
        nebari_version=__version__,
    )
    config.ci_cd.type = ci_provider
    config.terraform_state.type = terraform_state

    # Save default password to file
    default_password_filename = os.path.join(
        tempfile.gettempdir(), "NEBARI_DEFAULT_PASSWORD"
    )
    with open(default_password_filename, "w") as f:
        f.write(config.security.keycloak.initial_root_password)
    os.chmod(default_password_filename, 0o700)

    config.theme.jupyterhub.hub_title = f"Nebari - { project_name }"
    config.theme.jupyterhub.welcome = """Welcome! Learn about Nebari's features and configurations in <a href="https://www.nebari.dev/docs">the documentation</a>. If you have any questions or feedback, reach the team on <a href="https://www.nebari.dev/docs/community#getting-support">Nebari's support forums</a>."""

    config.security.authentication.type = auth_provider
    if config.security.authentication.type == schema.AuthenticationEnum.github:
        if not disable_prompt:
            config.security.authentication.config = schema.GithubConfig(
                client_id=input("Github client_id: "),
                client_secret=input("Github client_secret: "),
            )
    elif config.security.authentication.type == schema.AuthenticationEnum.auth0:
        if auth_auto_provision:
            auth0_config = create_client(config.domain, config.project_name)
            config.security.authentication.config = schema.Auth0Config(**auth0_config)
        else:
            config.security.authentication.config = schema.Auth0Config(
                client_id=input("Auth0 client_id: "),
                client_secret=input("Auth0 client_secret: "),
                auth0_subdomain=input("Auth0 subdomain: "),
            )

    if config.provider == schema.ProviderEnum.do:
        config.theme.jupyterhub.hub_subtitle = f"{WELCOME_HEADER_TEXT} on Digital Ocean"
    elif config.provider == schema.ProviderEnum.gcp:
        config.theme.jupyterhub.hub_subtitle = (
            f"{WELCOME_HEADER_TEXT} on Google Cloud Platform"
        )
        if "PROJECT_ID" in os.environ:
            config.google_cloud_platform.project = os.environ["PROJECT_ID"]
        elif not disable_prompt:
            config.google_cloud_platform.project = input(
                "Enter Google Cloud Platform Project ID: "
            )
    elif config.provider == schema.ProviderEnum.azure:
        config.theme.jupyterhub.hub_subtitle = f"{WELCOME_HEADER_TEXT} on Azure"
    elif config.provider == schema.ProviderEnum.aws:
        config.theme.jupyterhub.hub_subtitle = (
            f"{WELCOME_HEADER_TEXT} on Amazon Web Services"
        )
    elif cloud_provider == "existing":
        config.theme.jupyterhub.hub_subtitle = WELCOME_HEADER_TEXT
    elif cloud_provider == "local":
        config.theme.jupyterhub.hub_subtitle = WELCOME_HEADER_TEXT

    if ssl_cert_email:
        config.certificate.type = schema.CertificateEnum.letsencrypt
        config.certificate.acme_email = ssl_cert_email

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


def github_auto_provision(config: schema.Main, owner: str, repo: str):
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
                description=f"Nebari {config.project_name}-{config.provider}",
                homepage=f"https://{config.domain}",
            )
        except requests.exceptions.HTTPError as he:
            raise ValueError(
                f"Unable to create GitHub repo https://github.com/{owner}/{repo} - error message from GitHub is: {he}"
            )
    else:
        logger.warn(f"GitHub repo https://github.com/{owner}/{repo} already exists")

    try:
        # Secrets
        if config.provider == schema.ProviderEnum.do:
            for name in {
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "SPACES_ACCESS_KEY_ID",
                "SPACES_SECRET_ACCESS_KEY",
                "DIGITALOCEAN_TOKEN",
            }:
                github.update_secret(owner, repo, name, os.environ[name])
        elif config.provider == schema.ProviderEnum.aws:
            for name in {
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
            }:
                github.update_secret(owner, repo, name, os.environ[name])
        elif config.provider == schema.ProviderEnum.gcp:
            github.update_secret(owner, repo, "PROJECT_ID", os.environ["PROJECT_ID"])
            with open(os.environ["GOOGLE_CREDENTIALS"]) as f:
                github.update_secret(owner, repo, "GOOGLE_CREDENTIALS", f.read())
        elif config.provider == schema.ProviderEnum.azure:
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


def git_repository_initialize(git_repository: str):
    if not git.is_git_repo("./"):
        git.initialize_git("./")
    git.add_git_remote(git_repository, path="./", remote_name="origin")
