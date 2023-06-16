import os

import rich
import typer

from _nebari.cli.init import (
    check_project_name,
    check_ssl_cert_email,
    guided_init_wizard,
    handle_init,
)
from nebari import schema
from nebari.hookspecs import hookimpl

MISSING_CREDS_TEMPLATE = "Unable to locate your {provider} credentials, refer to this guide on how to generate them:\n\n[green]\t{link_to_docs}[/green]\n\n"
LINKS_TO_DOCS_TEMPLATE = (
    "For more details, refer to the Nebari docs:\n\n\t[green]{link_to_docs}[/green]\n\n"
)

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

# links to Nebari docs
DOCS_HOME = "https://nebari.dev/docs/"
CHOOSE_CLOUD_PROVIDER = "https://nebari.dev/docs/get-started/deploy"

GUIDED_INIT_MSG = (
    "[bold green]START HERE[/bold green] - this will guide you step-by-step "
    "to generate your [purple]nebari-config.yaml[/purple]. "
    "It is an [i]alternative[/i] to passing the options listed below."
)


def enum_to_list(enum_cls):
    return ", ".join([e.value.lower() for e in enum_cls])


def check_auth_provider_creds(ctx: typer.Context, auth_provider: str):
    """Validate the the necessary auth provider credentials have been set as environment variables."""
    if ctx.params.get("disable_prompt"):
        return auth_provider

    auth_provider = auth_provider.lower()

    # Auth0
    if auth_provider == schema.AuthenticationEnum.auth0.value.lower() and (
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
            "Paste your AUTH0_CLIENT_ID",
            hide_input=True,
        )
        os.environ["AUTH0_CLIENT_SECRET"] = typer.prompt(
            "Paste your AUTH0_CLIENT_SECRET",
            hide_input=True,
        )
        os.environ["AUTH0_DOMAIN"] = typer.prompt(
            "Paste your AUTH0_DOMAIN",
            hide_input=True,
        )

    # GitHub
    elif auth_provider == schema.AuthenticationEnum.github.value.lower() and (
        not os.environ.get("GITHUB_CLIENT_ID")
        or not os.environ.get("GITHUB_CLIENT_SECRET")
    ):
        rich.print(
            MISSING_CREDS_TEMPLATE.format(
                provider="GitHub OAuth App", link_to_docs=CREATE_GITHUB_OAUTH_CREDS
            )
        )

        os.environ["GITHUB_CLIENT_ID"] = typer.prompt(
            "Paste your GITHUB_CLIENT_ID",
            hide_input=True,
        )
        os.environ["GITHUB_CLIENT_SECRET"] = typer.prompt(
            "Paste your GITHUB_CLIENT_SECRET",
            hide_input=True,
        )

    return auth_provider


def check_cloud_provider_creds(ctx: typer.Context, cloud_provider: str):
    """Validate that the necessary cloud credentials have been set as environment variables."""
    if ctx.params.get("disable_prompt"):
        return cloud_provider

    cloud_provider = cloud_provider.lower()

    # AWS
    if cloud_provider == schema.ProviderEnum.aws.value.lower() and (
        not os.environ.get("AWS_ACCESS_KEY_ID")
        or not os.environ.get("AWS_SECRET_ACCESS_KEY")
    ):
        rich.print(
            MISSING_CREDS_TEMPLATE.format(
                provider="Amazon Web Services", link_to_docs=CREATE_AWS_CREDS
            )
        )

        os.environ["AWS_ACCESS_KEY_ID"] = typer.prompt(
            "Paste your AWS_ACCESS_KEY_ID",
            hide_input=True,
        )
        os.environ["AWS_SECRET_ACCESS_KEY"] = typer.prompt(
            "Paste your AWS_SECRET_ACCESS_KEY",
            hide_input=True,
        )

    # GCP
    elif cloud_provider == schema.ProviderEnum.gcp.value.lower() and (
        not os.environ.get("GOOGLE_CREDENTIALS") or not os.environ.get("PROJECT_ID")
    ):
        rich.print(
            MISSING_CREDS_TEMPLATE.format(
                provider="Google Cloud Provider", link_to_docs=CREATE_GCP_CREDS
            )
        )

        os.environ["GOOGLE_CREDENTIALS"] = typer.prompt(
            "Paste your GOOGLE_CREDENTIALS",
            hide_input=True,
        )
        os.environ["PROJECT_ID"] = typer.prompt(
            "Paste your PROJECT_ID",
            hide_input=True,
        )

    # DO
    elif cloud_provider == schema.ProviderEnum.do.value.lower() and (
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
            "Paste your DIGITALOCEAN_TOKEN",
            hide_input=True,
        )
        os.environ["SPACES_ACCESS_KEY_ID"] = typer.prompt(
            "Paste your SPACES_ACCESS_KEY_ID",
            hide_input=True,
        )
        os.environ["SPACES_SECRET_ACCESS_KEY"] = typer.prompt(
            "Paste your SPACES_SECRET_ACCESS_KEY",
            hide_input=True,
        )
        os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("SPACES_ACCESS_KEY_ID")
        os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY")

    # AZURE
    elif cloud_provider == schema.ProviderEnum.azure.value.lower() and (
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
            "Paste your ARM_CLIENT_ID",
            hide_input=True,
        )
        os.environ["ARM_SUBSCRIPTION_ID"] = typer.prompt(
            "Paste your ARM_SUBSCRIPTION_ID",
            hide_input=True,
        )
        os.environ["ARM_TENANT_ID"] = typer.prompt(
            "Paste your ARM_TENANT_ID",
            hide_input=True,
        )
        os.environ["ARM_CLIENT_SECRET"] = typer.prompt(
            "Paste your ARM_CLIENT_SECRET",
            hide_input=True,
        )

    return cloud_provider


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command()
    def init(
        cloud_provider: schema.ProviderEnum = typer.Argument(
            schema.ProviderEnum.local,
            help=f"options: {enum_to_list(schema.ProviderEnum)}",
            callback=check_cloud_provider_creds,
            is_eager=True,
        ),
        # Although this unused below, the functionality is contained in the callback. Thus,
        # this attribute cannot be removed.
        guided_init: bool = typer.Option(
            False,
            help=GUIDED_INIT_MSG,
            callback=guided_init_wizard,
            is_eager=True,
        ),
        project_name: str = typer.Option(
            ...,
            "--project-name",
            "--project",
            "-p",
            callback=check_project_name,
        ),
        domain_name: str = typer.Option(
            ...,
            "--domain-name",
            "--domain",
            "-d",
        ),
        namespace: str = typer.Option(
            "dev",
        ),
        auth_provider: schema.AuthenticationEnum = typer.Option(
            schema.AuthenticationEnum.password,
            help=f"options: {enum_to_list(schema.AuthenticationEnum)}",
            callback=check_auth_provider_creds,
        ),
        auth_auto_provision: bool = typer.Option(
            False,
        ),
        repository: schema.GitRepoEnum = typer.Option(
            None,
            help=f"options: {enum_to_list(schema.GitRepoEnum)}",
        ),
        repository_auto_provision: bool = typer.Option(
            False,
        ),
        ci_provider: schema.CiEnum = typer.Option(
            schema.CiEnum.none,
            help=f"options: {enum_to_list(schema.CiEnum)}",
        ),
        terraform_state: schema.TerraformStateEnum = typer.Option(
            schema.TerraformStateEnum.remote,
            help=f"options: {enum_to_list(schema.TerraformStateEnum)}",
        ),
        kubernetes_version: str = typer.Option(
            "latest",
        ),
        ssl_cert_email: str = typer.Option(
            None,
            callback=check_ssl_cert_email,
        ),
        disable_prompt: bool = typer.Option(
            False,
            is_eager=True,
        ),
    ):
        """
        Create and initialize your [purple]nebari-config.yaml[/purple] file.

        This command will create and initialize your [purple]nebari-config.yaml[/purple] :sparkles:

        This file contains all your Nebari cluster configuration details and,
        is used as input to later commands such as [green]nebari render[/green], [green]nebari deploy[/green], etc.

        If you're new to Nebari, we recommend you use the Guided Init wizard.
        To get started simply run:

                [green]nebari init --guided-init[/green]

        """
        inputs = schema.InitInputs()

        inputs.cloud_provider = cloud_provider
        inputs.project_name = project_name
        inputs.domain_name = domain_name
        inputs.namespace = namespace
        inputs.auth_provider = auth_provider
        inputs.auth_auto_provision = auth_auto_provision
        inputs.repository = repository
        inputs.repository_auto_provision = repository_auto_provision
        inputs.ci_provider = ci_provider
        inputs.terraform_state = terraform_state
        inputs.kubernetes_version = kubernetes_version
        inputs.ssl_cert_email = ssl_cert_email
        inputs.disable_prompt = disable_prompt

        handle_init(inputs)
