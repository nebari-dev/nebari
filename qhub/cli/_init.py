import os

import rich
import typer

from qhub.initialize import render_config
from qhub.schema import (
    AuthenticationEnum,
    InitInputs,
    ProviderEnum,
    project_name_convention,
)
from qhub.utils import QHUB_DASK_VERSION, QHUB_IMAGE_TAG, yaml

MISSING_CREDS_TEMPLATE = "Unable to locate your {provider} credentials, please refer to this guide on how to generate them:\n\n[light_green]\t\t{link_to_docs}[/light_green]\n\n"

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


def handle_init(inputs: InitInputs):
    if QHUB_IMAGE_TAG:
        print(
            f"Modifying the image tags for the `default_images`, setting tags equal to: {QHUB_IMAGE_TAG}"
        )

    if QHUB_DASK_VERSION:
        print(
            f"Modifying the version of the `qhub_dask` package, setting version equal to: {QHUB_DASK_VERSION}"
        )

    print(inputs)

    config = render_config(
        cloud_provider=inputs.cloud_provider,
        project_name=inputs.project_name,
        qhub_domain=inputs.domain_name,
        namespace=inputs.namespace,
        auth_provider=inputs.auth_provider,
        auth_auto_provision=inputs.auth_auto_provision,
        ci_provider=inputs.ci_provider,
        repository=inputs.repository,
        repository_auto_provision=inputs.repository_auto_provision,
        kubernetes_version=inputs.kubernetes_version,
        terraform_state=inputs.terraform_state,
        ssl_cert_email=inputs.ssl_cert_email,
        disable_prompt=False,  # keep?
    )

    try:
        with open("qhub-config.yaml", "x") as f:
            yaml.dump(config, f)
    except FileExistsError:
        raise ValueError(
            "A qhub-config.yaml file already exists. Please move or delete it and try again."
        )


def check_cloud_provider_creds(ctx: typer.Context, cloud_provider: str):
    """Validate that the necessary cloud credentials have been set as environment variables."""

    cloud_provider = cloud_provider.lower()

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

        os.environ["AWS_ACCESS_KEY_ID"] = typer.prompt(
            "Please enter your AWS_ACCESS_KEY_ID",
            hide_input=True,
        )
        os.environ["AWS_SECRET_ACCESS_KEY"] = typer.prompt(
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

        os.environ["GOOGLE_CREDENTIALS"] = typer.prompt(
            "Please enter your GOOGLE_CREDENTIALS",
            hide_input=True,
        )
        os.environ["PROJECT_ID"] = typer.prompt(
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

        os.environ["DIGITALOCEAN_TOKEN"] = typer.prompt(
            "Please enter your DIGITALOCEAN_TOKEN",
            hide_input=True,
        )
        os.environ["SPACES_ACCESS_KEY_ID"] = typer.prompt(
            "Please enter your SPACES_ACCESS_KEY_ID",
            hide_input=True,
        )
        os.environ["SPACES_SECRET_ACCESS_KEY"] = typer.prompt(
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

        os.environ["ARM_CLIENT_ID"] = typer.prompt(
            "Please enter your ARM_CLIENT_ID",
            hide_input=True,
        )
        os.environ["ARM_CLIENT_SECRET"] = typer.prompt(
            "Please enter your ARM_CLIENT_SECRET",
            hide_input=True,
        )
        os.environ["ARM_SUBSCRIPTION_ID"] = typer.prompt(
            "Please enter your ARM_SUBSCRIPTION_ID",
            hide_input=True,
        )
        os.environ["ARM_TENANT_ID"] = typer.prompt(
            "Please enter your ARM_TENANT_ID",
            hide_input=True,
        )

    return cloud_provider


def check_auth_provider_creds(ctx: typer.Context, auth_provider: str):
    """Validating the the necessary auth provider credentials have been set as environment variables."""

    auth_provider = auth_provider.lower()

    # Auth0
    if auth_provider == AuthenticationEnum.auth0.value.lower() and (
        not os.environ.get("AUTH0_CLIENT_ID")
        or not os.environ.get("AUTH0_CLIENT_SECRET")
        or not os.environ.get("AUTH0_DOMAIN")
    ):
        rich.print(
            MISSING_CREDS_TEMPLATE.format(
                provider="Auth0", link_to_docs=CREATE_AUTH0_CREDS
            )
        )

        os.environ["AUTH0_CLIENT_ID"] = typer.prompt(
            "Please enter your AUTH0_CLIENT_ID",
            hide_input=True,
        )
        os.environ["AUTH0_CLIENT_SECRET"] = typer.prompt(
            "Please enter your AUTH0_CLIENT_SECRET",
            hide_input=True,
        )
        os.environ["AUTH0_DOMAIN"] = typer.prompt(
            "Please enter your AUTH0_DOMAIN",
            hide_input=True,
        )

    # GitHub
    elif auth_provider == AuthenticationEnum.github.value.lower() and (
        not os.environ.get("GITHUB_CLIENT_ID")
        or not os.environ.get("GITHUB_CLIENT_SECRET")
    ):

        rich.print(
            MISSING_CREDS_TEMPLATE.format(
                provider="GitHub OAuth App", link_to_docs=CREATE_GITHUB_OAUTH_CREDS
            )
        )

        os.environ["GITHUB_CLIENT_ID"] = typer.prompt(
            "Please enter your GITHUB_CLIENT_ID",
            hide_input=True,
        )
        os.environ["GITHUB_CLIENT_SECRET"] = typer.prompt(
            "Please enter your GITHUB_CLIENT_SECRET",
            hide_input=True,
        )

    return auth_provider


def check_project_name(ctx: typer.Context, project_name: str):
    """Validate the project_name is acceptable. Depends on `cloud_provider`."""

    project_name_convention(
        project_name.lower(), {"provider": ctx.params["cloud_provider"]}
    )

    return project_name
