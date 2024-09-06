import enum
import os
import pathlib
import re
from typing import Optional

import questionary
import rich
import typer
from pydantic import BaseModel

from _nebari.config import write_configuration
from _nebari.constants import (
    AWS_DEFAULT_REGION,
    AZURE_DEFAULT_REGION,
    DO_DEFAULT_REGION,
    GCP_DEFAULT_REGION,
)
from _nebari.initialize import render_config
from _nebari.provider.cloud import (
    amazon_web_services,
    azure_cloud,
    digital_ocean,
    google_cloud,
)
from _nebari.stages.bootstrap import CiEnum
from _nebari.stages.kubernetes_keycloak import AuthenticationEnum
from _nebari.stages.terraform_state import TerraformStateEnum
from _nebari.utils import get_latest_kubernetes_version
from nebari import schema
from nebari.hookspecs import hookimpl
from nebari.schema import ProviderEnum

MISSING_CREDS_TEMPLATE = "Unable to locate your {provider} credentials, refer to this guide on how to generate them:\n\n[green]\t{link_to_docs}[/green]\n\n"
LINKS_TO_DOCS_TEMPLATE = (
    "For more details, refer to the Nebari docs:\n\n\t[green]{link_to_docs}[/green]\n\n"
)
LINKS_TO_EXTERNAL_DOCS_TEMPLATE = "For more details, refer to the {provider} docs:\n\n\t[green]{link_to_docs}[/green]\n\n"

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
AWS_REGIONS = "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-regions"
GCP_REGIONS = "https://cloud.google.com/compute/docs/regions-zones"
AZURE_REGIONS = "https://azure.microsoft.com/en-us/explore/global-infrastructure/geographies/#overview"
DO_REGIONS = (
    "https://docs.digitalocean.com/products/platform/availability-matrix/#regions"
)

# links to Nebari docs
DOCS_HOME = "https://nebari.dev/docs/"
CHOOSE_CLOUD_PROVIDER = "https://nebari.dev/docs/get-started/deploy"

GUIDED_INIT_MSG = (
    "[bold green]START HERE[/bold green] - this will guide you step-by-step "
    "to generate your [purple]nebari-config.yaml[/purple]. "
    "It is an [i]alternative[/i] to passing the options listed below."
)

DEFAULT_REGION_MSG = "Defaulting to region:`{region}`."

DEFAULT_KUBERNETES_VERSION_MSG = (
    "Defaulting to highest supported Kubernetes version: `{kubernetes_version}`."
)

LATEST = "latest"

CLOUD_PROVIDER_FULL_NAME = {
    "Local": ProviderEnum.local.name,
    "Existing": ProviderEnum.existing.name,
    "Digital Ocean": ProviderEnum.do.name,
    "Amazon Web Services": ProviderEnum.aws.name,
    "Google Cloud Platform": ProviderEnum.gcp.name,
    "Microsoft Azure": ProviderEnum.azure.name,
}


class GitRepoEnum(str, enum.Enum):
    github = "github.com"
    gitlab = "gitlab.com"


class InitInputs(schema.Base):
    cloud_provider: ProviderEnum = ProviderEnum.local
    project_name: schema.project_name_pydantic = ""
    domain_name: Optional[str] = None
    namespace: Optional[schema.namespace_pydantic] = "dev"
    auth_provider: AuthenticationEnum = AuthenticationEnum.password
    auth_auto_provision: bool = False
    repository: Optional[schema.github_url_pydantic] = None
    repository_auto_provision: bool = False
    ci_provider: CiEnum = CiEnum.none
    terraform_state: TerraformStateEnum = TerraformStateEnum.remote
    kubernetes_version: Optional[str] = None
    region: Optional[str] = None
    ssl_cert_email: Optional[schema.email_pydantic] = None
    disable_prompt: bool = False
    output: pathlib.Path = pathlib.Path("nebari-config.yaml")
    explicit: int = 0


def enum_to_list(enum_cls):
    return [e.value for e in enum_cls]


def get_region_docs(cloud_provider: str):
    if cloud_provider == ProviderEnum.aws.value.lower():
        return AWS_REGIONS
    elif cloud_provider == ProviderEnum.gcp.value.lower():
        return GCP_REGIONS
    elif cloud_provider == ProviderEnum.azure.value.lower():
        return AZURE_REGIONS
    elif cloud_provider == ProviderEnum.do.value.lower():
        return DO_REGIONS


def handle_init(inputs: InitInputs, config_schema: BaseModel):
    """
    Take the inputs from the `nebari init` command, render the config and write it to a local yaml file.
    """

    # this will force the `set_kubernetes_version` to grab the latest version
    if inputs.kubernetes_version == "latest":
        inputs.kubernetes_version = None

    config = render_config(
        cloud_provider=inputs.cloud_provider,
        project_name=inputs.project_name,
        nebari_domain=inputs.domain_name,
        namespace=inputs.namespace,
        auth_provider=inputs.auth_provider,
        auth_auto_provision=inputs.auth_auto_provision,
        ci_provider=inputs.ci_provider,
        repository=inputs.repository,
        repository_auto_provision=inputs.repository_auto_provision,
        kubernetes_version=inputs.kubernetes_version,
        region=inputs.region,
        terraform_state=inputs.terraform_state,
        ssl_cert_email=inputs.ssl_cert_email,
        disable_prompt=inputs.disable_prompt,
    )

    try:
        write_configuration(
            inputs.output,
            config if not inputs.explicit else config_schema(**config),
            mode="x",
        )
    except FileExistsError:
        raise ValueError(
            "A nebari-config.yaml file already exists. Please move or delete it and try again."
        )


def check_repository_creds(ctx: typer.Context, git_provider: str):
    """Validate the necessary Git provider (GitHub) credentials are set."""

    if (
        git_provider == GitRepoEnum.github.value.lower()
        and not os.environ.get("GITHUB_USERNAME")
        or not os.environ.get("GITHUB_TOKEN")
    ):
        os.environ["GITHUB_USERNAME"] = typer.prompt(
            "Paste your GITHUB_USERNAME",
            hide_input=True,
        )
        os.environ["GITHUB_TOKEN"] = typer.prompt(
            "Paste your GITHUB_TOKEN",
            hide_input=True,
        )


def typer_validate_regex(regex: str, error_message: str = None):
    def callback(value):
        if value is None:
            return value

        if re.fullmatch(regex, value):
            return value
        message = error_message or f"Does not match {regex}"
        raise typer.BadParameter(message)

    return callback


def questionary_validate_regex(regex: str, error_message: str = None):
    def callback(value):
        if re.fullmatch(regex, value):
            return True

        message = error_message or f"Invalid input. Does not match {regex}"
        return message

    return callback


def check_auth_provider_creds(ctx: typer.Context, auth_provider: str):
    """Validate the the necessary auth provider credentials have been set as environment variables."""
    if ctx.params.get("disable_prompt"):
        return auth_provider.lower()

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

        if not os.environ.get("AUTH0_CLIENT_ID"):
            os.environ["AUTH0_CLIENT_ID"] = typer.prompt(
                "Paste your AUTH0_CLIENT_ID",
                hide_input=True,
            )

        if not os.environ.get("AUTH0_CLIENT_SECRET"):
            os.environ["AUTH0_CLIENT_SECRET"] = typer.prompt(
                "Paste your AUTH0_CLIENT_SECRET",
                hide_input=True,
            )

        if not os.environ.get("AUTH0_DOMAIN"):
            os.environ["AUTH0_DOMAIN"] = typer.prompt(
                "Paste your AUTH0_DOMAIN",
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

        if not os.environ.get("GITHUB_CLIENT_ID"):
            os.environ["GITHUB_CLIENT_ID"] = typer.prompt(
                "Paste your GITHUB_CLIENT_ID",
                hide_input=True,
            )

        if not os.environ.get("GITHUB_CLIENT_SECRET"):
            os.environ["GITHUB_CLIENT_SECRET"] = typer.prompt(
                "Paste your GITHUB_CLIENT_SECRET",
                hide_input=True,
            )

    return auth_provider


def check_cloud_provider_creds(cloud_provider: ProviderEnum, disable_prompt: bool):
    """Validate that the necessary cloud credentials have been set as environment variables."""

    if disable_prompt:
        return cloud_provider.lower()

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
            "Paste your AWS_ACCESS_KEY_ID",
            hide_input=True,
        )
        os.environ["AWS_SECRET_ACCESS_KEY"] = typer.prompt(
            "Paste your AWS_SECRET_ACCESS_KEY",
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
            "Paste your GOOGLE_CREDENTIALS",
            hide_input=True,
        )
        os.environ["PROJECT_ID"] = typer.prompt(
            "Paste your PROJECT_ID",
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
        # Set spaces credentials. Spaces are API compatible with s3
        # Setting spaces credentials to AWS credentials allows us to
        # reuse s3 code
        os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("SPACES_ACCESS_KEY_ID")
        os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("SPACES_SECRET_ACCESS_KEY")

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


def check_cloud_provider_kubernetes_version(
    kubernetes_version: str, cloud_provider: str, region: str
):
    if cloud_provider == ProviderEnum.aws.value.lower():
        versions = amazon_web_services.kubernetes_versions(region)

        if not kubernetes_version or kubernetes_version == LATEST:
            kubernetes_version = get_latest_kubernetes_version(versions)
            rich.print(
                DEFAULT_KUBERNETES_VERSION_MSG.format(
                    kubernetes_version=kubernetes_version
                )
            )
        if kubernetes_version not in versions:
            raise ValueError(
                f"Invalid Kubernetes version `{kubernetes_version}`. Please refer to the AWS docs for a list of valid versions: {versions}"
            )
    elif cloud_provider == ProviderEnum.azure.value.lower():
        versions = azure_cloud.kubernetes_versions(region)

        if not kubernetes_version or kubernetes_version == LATEST:
            kubernetes_version = get_latest_kubernetes_version(versions)
            rich.print(
                DEFAULT_KUBERNETES_VERSION_MSG.format(
                    kubernetes_version=kubernetes_version
                )
            )
        if kubernetes_version not in versions:
            raise ValueError(
                f"Invalid Kubernetes version `{kubernetes_version}`. Please refer to the Azure docs for a list of valid versions: {versions}"
            )
    elif cloud_provider == ProviderEnum.gcp.value.lower():
        versions = google_cloud.kubernetes_versions(region)

        if not kubernetes_version or kubernetes_version == LATEST:
            kubernetes_version = get_latest_kubernetes_version(versions)
            rich.print(
                DEFAULT_KUBERNETES_VERSION_MSG.format(
                    kubernetes_version=kubernetes_version
                )
            )
        if kubernetes_version not in versions:
            raise ValueError(
                f"Invalid Kubernetes version `{kubernetes_version}`. Please refer to the GCP docs for a list of valid versions: {versions}"
            )
    elif cloud_provider == ProviderEnum.do.value.lower():
        versions = digital_ocean.kubernetes_versions()

        if not kubernetes_version or kubernetes_version == LATEST:
            kubernetes_version = get_latest_kubernetes_version(versions)
            rich.print(
                DEFAULT_KUBERNETES_VERSION_MSG.format(
                    kubernetes_version=kubernetes_version
                )
            )
        if kubernetes_version not in versions:
            raise ValueError(
                f"Invalid Kubernetes version `{kubernetes_version}`. Please refer to the DO docs for a list of valid versions: {versions}"
            )

    return kubernetes_version


def check_cloud_provider_region(region: str, cloud_provider: str) -> str:
    if cloud_provider == ProviderEnum.aws.value.lower():
        if not region:
            region = os.environ.get("AWS_DEFAULT_REGION")
            if not region:
                region = AWS_DEFAULT_REGION
                rich.print(f"Defaulting to `{region}` region.")
            else:
                rich.print(
                    f"Falling back to the region found in the AWS_DEFAULT_REGION environment variable: `{region}`"
                )
        region = amazon_web_services.validate_region(region)
    elif cloud_provider == ProviderEnum.azure.value.lower():
        # TODO: Add a check for valid region for Azure
        if not region:
            region = AZURE_DEFAULT_REGION
            rich.print(DEFAULT_REGION_MSG.format(region=region))
    elif cloud_provider == ProviderEnum.gcp.value.lower():
        if not region:
            region = GCP_DEFAULT_REGION
            rich.print(DEFAULT_REGION_MSG.format(region=region))
        if region not in google_cloud.regions():
            raise ValueError(
                f"Invalid region `{region}`. Please refer to the GCP docs for a list of valid regions: {GCP_REGIONS}"
            )
    elif cloud_provider == ProviderEnum.do.value.lower():
        if not region:
            region = DO_DEFAULT_REGION
            rich.print(DEFAULT_REGION_MSG.format(region=region))

        if region not in set(_["slug"] for _ in digital_ocean.regions()):
            raise ValueError(
                f"Invalid region `{region}`. Please refer to the DO docs for a list of valid regions: {DO_REGIONS}"
            )
    return region


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command()
    def init(
        cloud_provider: ProviderEnum = typer.Argument(
            ProviderEnum.local,
            help=f"options: {enum_to_list(ProviderEnum)}",
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
            callback=typer_validate_regex(
                schema.project_name_regex,
                "Project name must (1) consist of only letters, numbers, hyphens, and underscores, (2) begin and end with a letter, and (3) contain between 3 and 16 characters.",
            ),
        ),
        domain_name: Optional[str] = typer.Option(
            None,
            "--domain-name",
            "--domain",
            "-d",
        ),
        namespace: str = typer.Option(
            "dev",
            callback=typer_validate_regex(
                schema.namespace_regex,
                "Namespace must begin and end with a letter and consist of letters, dashes, or underscores.",
            ),
        ),
        region: str = typer.Option(
            None,
            help="The region you want to deploy your Nebari cluster to (if deploying to the cloud)",
        ),
        auth_provider: AuthenticationEnum = typer.Option(
            AuthenticationEnum.password,
            help=f"options: {enum_to_list(AuthenticationEnum)}",
            callback=check_auth_provider_creds,
        ),
        auth_auto_provision: bool = typer.Option(
            False,
        ),
        repository: str = typer.Option(
            None,
            help="Github repository URL to be initialized with --repository-auto-provision",
            callback=typer_validate_regex(
                schema.github_url_regex,
                "Must be a fully qualified GitHub repository URL.",
            ),
        ),
        repository_auto_provision: bool = typer.Option(
            False,
            help="Initialize the GitHub repository provided by --repository (GitHub credentials required)",
        ),
        ci_provider: CiEnum = typer.Option(
            CiEnum.none,
            help=f"options: {enum_to_list(CiEnum)}",
        ),
        terraform_state: TerraformStateEnum = typer.Option(
            TerraformStateEnum.remote,
            help=f"options: {enum_to_list(TerraformStateEnum)}",
        ),
        kubernetes_version: str = typer.Option(
            LATEST,
            help="The Kubernetes version you want to deploy your Nebari cluster to, leave blank for latest version",
        ),
        ssl_cert_email: str = typer.Option(
            None,
            callback=typer_validate_regex(
                schema.email_regex,
                f"Email must be valid and match the regex {schema.email_regex}",
            ),
        ),
        disable_prompt: bool = typer.Option(
            False,
            is_eager=True,
        ),
        output: str = typer.Option(
            pathlib.Path("nebari-config.yaml"),
            "--output",
            "-o",
            help="Output file path for the rendered config file.",
        ),
        explicit: int = typer.Option(
            0,
            "--explicit",
            "-e",
            count=True,
            help="Write explicit nebari config file (advanced users only).",
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
        inputs = InitInputs()

        # validate inputs after they've been set so we can control the order they are validated
        # validations for --guided-init should be handled as a callbacks within the `guided_init_wizard`
        inputs.cloud_provider = check_cloud_provider_creds(
            cloud_provider, disable_prompt
        )

        # Digital Ocean deprecation warning -- Nebari 2024.7.1
        if inputs.cloud_provider == ProviderEnum.do.value.lower():
            rich.print(
                ":warning: Digital Ocean support is being deprecated and support will be removed in the future. :warning:\n"
            )

        inputs.region = check_cloud_provider_region(region, inputs.cloud_provider)
        inputs.kubernetes_version = check_cloud_provider_kubernetes_version(
            kubernetes_version, inputs.cloud_provider, inputs.region
        )

        inputs.project_name = project_name
        inputs.domain_name = domain_name
        inputs.namespace = namespace
        inputs.auth_provider = auth_provider
        inputs.auth_auto_provision = auth_auto_provision
        inputs.repository = repository
        inputs.repository_auto_provision = repository_auto_provision
        inputs.ci_provider = ci_provider
        inputs.terraform_state = terraform_state
        inputs.ssl_cert_email = ssl_cert_email
        inputs.disable_prompt = disable_prompt
        inputs.output = output
        inputs.explicit = explicit

        from nebari.plugins import nebari_plugin_manager

        handle_init(inputs, config_schema=nebari_plugin_manager.config_schema)

        nebari_plugin_manager.read_config(output)


def guided_init_wizard(ctx: typer.Context, guided_init: str):
    """
    Guided Init Wizard is a user-friendly questionnaire used to help generate the `nebari-config.yaml`.
    """
    qmark = "  "
    disable_checks = os.environ.get("NEBARI_DISABLE_INIT_CHECKS", False)

    if not guided_init:
        return guided_init

    if pathlib.Path("nebari-config.yaml").exists():
        raise ValueError(
            "A nebari-config.yaml file already exists. Please move or delete it and try again."
        )

    try:
        rich.print(
            (
                "\n\t[bold]Welcome to the Guided Init wizard![/bold]\n\n"
                "You will be asked a few questions to generate your [purple]nebari-config.yaml[/purple]. "
                f"{LINKS_TO_DOCS_TEMPLATE.format(link_to_docs=DOCS_HOME)}"
            )
        )

        if disable_checks:
            rich.print(
                "⚠️  Attempting to use the Guided Init wizard without any validation checks. There is no guarantee values provided will work!  ⚠️\n\n"
            )

        # pull in default values for each of the below
        inputs = InitInputs()

        # CLOUD PROVIDER
        rich.print(
            (
                "\n 🪴  Nebari runs on a Kubernetes cluster: Where do you want this Kubernetes cluster deployed? "
                "is where you want this Kubernetes cluster deployed. "
                f"{LINKS_TO_DOCS_TEMPLATE.format(link_to_docs=CHOOSE_CLOUD_PROVIDER)}"
                "\n\t❗️ [purple]local[/purple] requires Docker and Kubernetes running on your local machine. "
                "[italic]Currently only available on Linux OS.[/italic]"
                "\n\t❗️ [purple]existing[/purple] refers to an existing Kubernetes cluster that Nebari can be deployed on.\n"
                "\n\t❗️ [red]Digital Ocean[/red] is currently being deprecated and support will be removed in the future.\n"
            )
        )
        # try:
        cloud_provider: str = questionary.select(
            "Where would you like to deploy your Nebari cluster?",
            choices=CLOUD_PROVIDER_FULL_NAME.keys(),
            qmark=qmark,
        ).unsafe_ask()

        inputs.cloud_provider = CLOUD_PROVIDER_FULL_NAME.get(cloud_provider)

        if not disable_checks:
            check_cloud_provider_creds(
                cloud_provider=inputs.cloud_provider,
                disable_prompt=ctx.params.get("disable_prompt"),
            )

        # specific context needed when `check_project_name` is called
        ctx.params["cloud_provider"] = inputs.cloud_provider

        # cloud region
        if (
            inputs.cloud_provider != ProviderEnum.local.value.lower()
            and inputs.cloud_provider != ProviderEnum.existing.value.lower()
        ):
            aws_region = os.environ.get("AWS_DEFAULT_REGION")
            if inputs.cloud_provider == ProviderEnum.aws.value.lower() and aws_region:
                region = aws_region
            else:
                region_docs = get_region_docs(inputs.cloud_provider)
                rich.print(
                    (
                        "\n 🪴  Nebari clusters that run in the cloud require specifying which region to deploy to, "
                        "please review the the cloud provider docs on the names and format these region take "
                        f"{LINKS_TO_EXTERNAL_DOCS_TEMPLATE.format(provider=inputs.cloud_provider.value, link_to_docs=region_docs)}"
                    )
                )

                region = questionary.text(
                    "In which region would you like to deploy your Nebari cluster?",
                    qmark=qmark,
                ).unsafe_ask()

            if not disable_checks:
                region = check_cloud_provider_region(
                    region, cloud_provider=inputs.cloud_provider
                )

            inputs.region = region
            ctx.params["region"] = region

        name_guidelines = """
        The project name must adhere to the following requirements:
        - Letters from A to Z (upper and lower case), numbers, hyphens, and dashes
        - Length from 3 to 16 characters
        - Begin and end with a letter
        """

        # PROJECT NAME
        rich.print(
            (
                f"\n 🪴  Next, give your Nebari instance a project name. This name is what your Kubernetes cluster will be referred to as.\n{name_guidelines}\n"
            )
        )
        inputs.project_name = questionary.text(
            "What project name would you like to use?",
            qmark=qmark,
            validate=questionary_validate_regex(schema.project_name_regex),
        ).unsafe_ask()

        # DOMAIN NAME
        rich.print(
            (
                "\n\n 🪴  Great! Now you can provide a valid domain name (i.e. the URL) to access your Nebari instance. "
                "This should be a domain that you own. Default if unspecified is the IP of the load balancer.\n\n"
            )
        )
        inputs.domain_name = (
            questionary.text(
                "What domain name would you like to use?",
                qmark=qmark,
            ).unsafe_ask()
            or None
        )

        # AUTH PROVIDER
        rich.print(
            (
                # TODO once docs are updated, add links for more details
                "\n\n 🪴  Nebari comes with [green]Keycloak[/green], an open-source identity and access management tool. This is how users and permissions "
                "are managed on the platform. To connect Keycloak with an identity provider, you can select one now.\n\n"
                "\n\t❗️ [purple]password[/purple] is the default option and is not connected to any external identity provider.\n"
            )
        )
        inputs.auth_provider = questionary.select(
            "What authentication provider would you like?",
            choices=enum_to_list(AuthenticationEnum),
            qmark=qmark,
        ).unsafe_ask()

        if not disable_checks:
            check_auth_provider_creds(ctx, auth_provider=inputs.auth_provider)

        if inputs.auth_provider.lower() == AuthenticationEnum.auth0.value.lower():
            inputs.auth_auto_provision = questionary.confirm(
                "Would you like us to auto provision the Auth0 Machine-to-Machine app?",
                default=False,
                qmark=qmark,
                auto_enter=False,
            ).unsafe_ask()

        elif inputs.auth_provider.lower() == AuthenticationEnum.github.value.lower():
            rich.print(
                (
                    ":warning: If you haven't done so already, please ensure the following:\n"
                    f"The `Homepage URL` is set to: [green]https://{inputs.domain_name}[/green]\n"
                    f"The `Authorization callback URL` is set to: [green]https://{inputs.domain_name}/auth/realms/nebari/broker/github/endpoint[/green]\n\n"
                )
            )

        # GITOPS - REPOSITORY, CICD
        rich.print(
            (
                "\n\n 🪴  This next section is [italic]optional[/italic] but recommended. If you wish to adopt a GitOps approach to managing this platform, "
                "we will walk you through a set of questions to get that setup. With this setup, Nebari will use GitHub Actions workflows (or GitLab equivalent) "
                "to automatically handle the future deployments of your infrastructure.\n\n"
            )
        )
        if questionary.confirm(
            "Would you like to adopt a GitOps approach to managing Nebari?",
            default=False,
            qmark=qmark,
            auto_enter=False,
        ).unsafe_ask():
            repo_url = "https://{git_provider}/{org_name}/{repo_name}"

            git_provider = questionary.select(
                "Which git provider would you like to use?",
                choices=enum_to_list(GitRepoEnum),
                qmark=qmark,
            ).unsafe_ask()

            if git_provider == GitRepoEnum.github.value.lower():
                inputs.ci_provider = CiEnum.github_actions.value.lower()

                inputs.repository_auto_provision = questionary.confirm(
                    f"Would you like nebari to create a remote repository on {git_provider}?",
                    default=False,
                    qmark=qmark,
                    auto_enter=False,
                ).unsafe_ask()

                if inputs.repository_auto_provision:
                    org_name = questionary.text(
                        f"Which user or organization will this repository live under? ({repo_url.format(git_provider=git_provider, org_name='<org-name>', repo_name='')})",
                        qmark=qmark,
                    ).unsafe_ask()

                    repo_name = questionary.text(
                        f"And what will the name of this repository be? ({repo_url.format(git_provider=git_provider, org_name=org_name, repo_name='<repo-name>')})",
                        qmark=qmark,
                    ).unsafe_ask()

                    inputs.repository = repo_url.format(
                        git_provider=git_provider,
                        org_name=org_name,
                        repo_name=repo_name,
                    )

                    if not disable_checks:
                        check_repository_creds(ctx, git_provider)

            elif git_provider == GitRepoEnum.gitlab.value.lower():
                inputs.ci_provider = CiEnum.gitlab_ci.value.lower()

        # SSL CERTIFICATE
        if inputs.domain_name:
            rich.print(
                (
                    "\n\n 🪴  This next section is [italic]optional[/italic] but recommended. If you want your Nebari domain to use a Let's Encrypt SSL certificate, "
                    "all we need is an email address from you.\n\n"
                )
            )
            ssl_cert = questionary.confirm(
                "Would you like to add a Let's Encrypt SSL certificate to your domain?",
                default=False,
                qmark=qmark,
                auto_enter=False,
            ).unsafe_ask()

            if ssl_cert:
                inputs.ssl_cert_email = questionary.text(
                    "Which email address should Let's Encrypt associate the certificate with?",
                    qmark=qmark,
                ).unsafe_ask()

                if not disable_checks:
                    typer_validate_regex(
                        schema.email_regex,
                        f"Email must be valid and match the regex {schema.email_regex}",
                    )

        # ADVANCED FEATURES
        rich.print(
            (
                # TODO once docs are updated, add links for more info on these changes
                "\n\n 🪴  This next section is [italic]optional[/italic] and includes advanced configuration changes to the "
                "Terraform state, Kubernetes Namespace and Kubernetes version."
                "\n ⚠️  caution is advised!\n\n"
            )
        )
        if questionary.confirm(
            "Would you like to make advanced configuration changes?",
            default=False,
            qmark=qmark,
            auto_enter=False,
        ).unsafe_ask():
            # TERRAFORM STATE
            inputs.terraform_state = questionary.select(
                "Where should the Terraform State be provisioned?",
                choices=enum_to_list(TerraformStateEnum),
                qmark=qmark,
            ).unsafe_ask()

            # NAMESPACE
            inputs.namespace = questionary.text(
                "What would you like the main Kubernetes namespace to be called?",
                default=inputs.namespace,
                qmark=qmark,
            ).unsafe_ask()

            # KUBERNETES VERSION
            kubernetes_version = questionary.text(
                "Which Kubernetes version would you like to use (if none provided; latest version will be installed)?",
                qmark=qmark,
            ).unsafe_ask()
            if not disable_checks:
                check_cloud_provider_kubernetes_version(
                    kubernetes_version=kubernetes_version,
                    cloud_provider=inputs.cloud_provider,
                    region=inputs.region,
                )
            inputs.kubernetes_version = kubernetes_version

            # EXPLICIT CONFIG
            inputs.explicit = questionary.confirm(
                "Would you like the nebari config to show all available options? (recommended for advanced users only)",
                default=False,
                qmark=qmark,
                auto_enter=False,
            ).unsafe_ask()

        from nebari.plugins import nebari_plugin_manager

        config_schema = nebari_plugin_manager.config_schema

        handle_init(inputs, config_schema=config_schema)

        rich.print(
            (
                "\n\n\t:sparkles: [bold]Congratulations[/bold], you have generated the all important [purple]nebari-config.yaml[/purple] file :sparkles:\n\n"
                "You can always make changes to your [purple]nebari-config.yaml[/purple] file by editing the file directly.\n"
                "If you do make changes to it you can ensure it's still a valid configuration by running:\n\n"
                "\t[green]nebari validate --config path/to/nebari-config.yaml[/green]\n\n"
            )
        )

        base_cmd = f"nebari init {inputs.cloud_provider.value}"

        def if_used(key, model=inputs, ignore_list=["cloud_provider"]):
            if key not in ignore_list:
                value = getattr(model, key)
                if isinstance(value, enum.Enum):
                    return f"--{key} {value.value}".replace("_", "-")
                elif isinstance(value, bool):
                    if value:
                        return f"--{key}".replace("_", "-")
                elif isinstance(value, (int, str)):
                    if value:
                        return f"--{key} {value}".replace("_", "-")

        cmds = " ".join(
            [
                _
                for _ in [if_used(_) for _ in inputs.model_dump().keys()]
                if _ is not None
            ]
        )

        rich.print(
            (
                "For reference, if the previous Guided Init answers were converted into a direct [green]nebari init[/green] command, it would be:\n\n"
                f"\t[green]{base_cmd} {cmds}[/green]\n\n"
            )
        )

        rich.print(
            (
                "You can now deploy your Nebari instance with:\n\n"
                "\t[green]nebari deploy -c nebari-config.yaml[/green]\n\n"
                "For more information, run [green]nebari deploy --help[/green] or check out the documentation: "
                "[green]https://www.nebari.dev/docs/how-tos/[/green]"
            )
        )

    except KeyboardInterrupt:
        rich.print("\nUser quit the Guided Init.\n\n ")
        raise typer.Exit()

    raise typer.Exit()
