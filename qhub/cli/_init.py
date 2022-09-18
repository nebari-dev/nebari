import os
from pathlib import Path

import rich
import typer
from dotenv import load_dotenv

from qhub.schema import AuthenticationEnum, ProviderEnum, project_name_convention

MISSING_CREDS_TEMPLATE = "Unable to locate your {provider} credentials, please refer to this guide on how to generate them:\n[light_green]{link_to_docs}[/light_green]\n"

# links to external docs
CREATE_AWS_CREDS = (
    "https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html"
)
CREATE_GCP_CREDS = (
    "https://cloud.google.com/iam/docs/creating-managing-service-accounts"
)
CREATE_DO_CREDS = (
    "https://docs.digitalocean.com/reference/api/create-personal-access-token"
)
CREATE_AZURE_CREDS = "https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/service_principal_client_secret#creating-a-service-principal-in-the-azure-portal"
CREATE_AUTH0_CREDS = "https://auth0.com/docs/get-started/auth0-overview/create-applications/machine-to-machine-apps"
CREATE_GITHUB_OAUTH_CREDS = "https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app"


DOTENV_FILE = Path.cwd() / ".env"


def _load_dotenv(dotenv_file=DOTENV_FILE):
    load_dotenv(dotenv_file)


def add_env_var(env_vars: dict):

    new_line = "{key}={value}\n"

    if not DOTENV_FILE.exists():
        rich.print(
            (
                "Creating a `.env` file used to manage your cloud credentials"
                f"and other important tokens.\nYou can view them here: {DOTENV_FILE.resolve()}"
            )
        )

    with open(DOTENV_FILE, "a+") as f:
        for key, value in env_vars.items():
            rich.print(f"Writing {key} to `.env` file...")
            f.writelines(new_line.format(key=key, value=value))


def check_cloud_provider_creds(cloud_provider: str):
    """Validate that the necessary cloud credentials have been set as environment variables."""

    rich.print("Creating and initializing your nebari-config.yaml :rocket:\n")

    _load_dotenv()
    cloud_provider = cloud_provider.lower()
    env_vars = {}

    # AWS
    if cloud_provider == ProviderEnum.aws.value.lower() and (
        not os.environ.get("AWS_ACCESS_KEY_ID")
        or not os.environ.get("AWS_SECRET_ACCESS_KEY")
    ):
        rich.print(
            MISSING_CREDS_TEMPLATE.format(
                provider="Amazon Web Services", link_to_docs=CREATE_AWS_CREDS
            )
        )

        env_vars["AWS_ACCESS_KEY_ID"] = typer.prompt(
            "Please enter your AWS_ACCESS_KEY_ID",
            hide_input=True,
        )
        env_vars["AWS_SECRET_ACCESS_KEY"] = typer.prompt(
            "Please enter your AWS_SECRET_ACCESS_KEY",
            hide_input=True,
        )

    # GCP
    elif cloud_provider == ProviderEnum.gcp.value.lower() and (
        not os.environ.get("GOOGLE_CREDENTIALS") or not os.environ.get("PROJECT_ID")
    ):
        rich.print(
            MISSING_CREDS_TEMPLATE.format(
                provider="Google Cloud Provider", link_to_docs=CREATE_GCP_CREDS
            )
        )

        env_vars["GOOGLE_CREDENTIALS"] = typer.prompt(
            "Please enter your GOOGLE_CREDENTIALS",
            hide_input=True,
        )
        env_vars["PROJECT_ID"] = typer.prompt(
            "Please enter your PROJECT_ID",
            hide_input=True,
        )

    # DO
    elif cloud_provider == ProviderEnum.do.value.lower() and (
        not os.environ.get("DIGITALOCEAN_TOKEN")
        or not os.environ.get("SPACES_ACCESS_KEY_ID")
        or not os.environ.get("SPACES_SECRET_ACCESS_KEY")
    ):
        rich.print(
            MISSING_CREDS_TEMPLATE.format(
                provider="Digital Ocean", link_to_docs=CREATE_DO_CREDS
            )
        )

        env_vars["DIGITALOCEAN_TOKEN"] = typer.prompt(
            "Please enter your DIGITALOCEAN_TOKEN",
            hide_input=True,
        )
        env_vars["SPACES_ACCESS_KEY_ID"] = typer.prompt(
            "Please enter your SPACES_ACCESS_KEY_ID",
        )
        env_vars["SPACES_SECRET_ACCESS_KEY"] = typer.prompt(
            "Please enter your SPACES_SECRET_ACCESS_KEY",
            hide_input=True,
        )

    # AZURE
    elif cloud_provider == ProviderEnum.azure.value.lower() and (
        not os.environ.get("ARM_CLIENT_ID")
        or not os.environ.get("ARM_CLIENT_SECRET")
        or not os.environ.get("ARM_SUBSCRIPTION_ID")
        or not os.environ.get("ARM_TENANT_ID")
    ):
        rich.print(
            MISSING_CREDS_TEMPLATE.format(
                provider="Azure", link_to_docs=CREATE_AZURE_CREDS
            )
        )

        env_vars["ARM_CLIENT_ID"] = typer.prompt(
            "Please enter your ARM_CLIENT_ID",
            hide_input=True,
        )
        env_vars["ARM_CLIENT_SECRET"] = typer.prompt(
            "Please enter your ARM_CLIENT_SECRET",
            hide_input=True,
        )
        env_vars["ARM_SUBSCRIPTION_ID"] = typer.prompt(
            "Please enter your ARM_SUBSCRIPTION_ID",
            hide_input=True,
        )
        env_vars["ARM_TENANT_ID"] = typer.prompt(
            "Please enter your ARM_TENANT_ID",
            hide_input=True,
        )

    add_env_var(env_vars)
    _load_dotenv()

    return cloud_provider


def check_auth_provider_creds(ctx: typer.Context, auth_provider: str):
    """Validating the the necessary auth provider credentials have been set as environment variables."""

    _load_dotenv()
    env_vars = {}
    auth_provider = auth_provider.lower()

    # Auth0
    if auth_provider == AuthenticationEnum.auth0.value.lower():

        if (
            not os.environ.get("AUTH0_CLIENT_ID")
            or not os.environ.get("AUTH0_CLIENT_SECRET")
            or not os.environ.get("AUTH0_DOMAIN")
        ):
            rich.print(
                MISSING_CREDS_TEMPLATE.format(
                    provider="Auth0", link_to_docs=CREATE_AUTH0_CREDS
                )
            )

            env_vars["AUTH0_CLIENT_ID"] = typer.prompt(
                "Please enter your AUTH0_CLIENT_ID",
                hide_input=True,
            )
            env_vars["AUTH0_CLIENT_SECRET"] = typer.prompt(
                "Please enter your AUTH0_CLIENT_SECRET",
                hide_input=True,
            )
            env_vars["AUTH0_DOMAIN"] = typer.prompt(
                "Please enter your AUTH0_DOMAIN",
                hide_input=True,
            )

        if not ctx.params.get("auth_auto_provision", False):
            ctx.params["auth_auto_provision"] = typer.prompt(
                "Do you wish for Nebari to automatically provision the Auth0 `Regular Web Application`?",
                type=bool,
                default=True,
            )

    # GitHub
    elif auth_provider == AuthenticationEnum.github.value.lower():

        if not os.environ.get("GITHUB_CLIENT_ID") or not os.environ.get(
            "GITHUB_CLIENT_SECRET"
        ):

            rich.print(
                MISSING_CREDS_TEMPLATE.format(
                    provider="GitHub OAuth App", link_to_docs=CREATE_GITHUB_OAUTH_CREDS
                )
            )

            env_vars["GITHUB_CLIENT_ID"] = typer.prompt(
                "Please enter your GITHUB_CLIENT_ID",
                hide_input=True,
            )
            env_vars["GITHUB_CLIENT_SECRET"] = typer.prompt(
                "Please enter your GITHUB_CLIENT_SECRET",
                hide_input=True,
            )

        domain_name = ctx.params.get("domain_name", "<your-domain-name>")
        rich.print(
            (
                ":warning: If you haven't done so already, please ensure the following:\n"
                f"The `Homepage URL` is set to: [light_green]https://{domain_name}[/light_green]\n"
                f"The `Authorization callback URL` is set to: [light_green]https://{domain_name}/auth/realms/qhub/broker/github/endpoint[/light_green]\n\n"
            )
        )

    add_env_var(env_vars)
    _load_dotenv()

    return auth_provider


def check_project_name(ctx: typer.Context, project_name: str):
    project_name_convention(
        project_name.lower(), {"provider": ctx.params["cloud_provider"]}
    )

    return project_name
