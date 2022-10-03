import os

import questionary
import rich
import typer

from qhub.initialize import render_config
from qhub.schema import (
    AuthenticationEnum,
    CiEnum,
    InitInputs,
    ProviderEnum,
    TerraformStateEnum,
    project_name_convention,
)
from qhub.utils import QHUB_DASK_VERSION, QHUB_IMAGE_TAG, yaml

MISSING_CREDS_TEMPLATE = "Unable to locate your {provider} credentials, refer to this guide on how to generate them:\n\n[light_green]\t\t{link_to_docs}[/light_green]\n\n"
LINKS_TO_DOCS_TEMPLATE = "For more details, refer to the Nebari docs:\n\n\t[light_green]{link_to_docs}[/light_green]\n\n"

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
DOCS_HOME = "https://nebari-docs.netlify.app"
CHOOSE_CLOUD_PROVIDER = "https://nebari-docs.netlify.app/getting-started/deploy"


def enum_to_list(enum_cls):
    return [e.value.lower() for e in enum_cls]


def handle_init(inputs: InitInputs):
    if QHUB_IMAGE_TAG:
        print(
            f"Modifying the image tags for the `default_images`, setting tags to: {QHUB_IMAGE_TAG}"
        )

    if QHUB_DASK_VERSION:
        print(
            f"Modifying the version of the `qhub_dask` package, setting version to: {QHUB_DASK_VERSION}"
        )

    # this will force the `set_kubernetes_version` to grab the latest version
    if inputs.kubernetes_version == "latest":
        inputs.kubernetes_version = None

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


def guided_init_wizard(ctx: typer.Context, guided_init: str):
    """
    Guided Init Wizard is a user-friendly questionnaire used to help generate the `nebari-config.yaml`.
    """
    qmark = "  "
    disable_checks = os.environ.get("QHUB_DISABLE_INIT_CHECKS", False)

    if not guided_init:
        return guided_init

    rich.print(
        (
            "\n\t\t[bold]Welcome to the Guided Init wizard![/bold]\n\n"
            "You will be asked a few questions that are used to generate your [purple]nebari-config.yaml[/purple]. "
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
            "\n 🪴  Nebari runs on a Kubernetes cluster so one of the first choices that needs to be made "
            "is where you want this Kubernetes cluster deployed. "
            f"{LINKS_TO_DOCS_TEMPLATE.format(link_to_docs=CHOOSE_CLOUD_PROVIDER)}"
            "\n\t❕ [purple]local[/purple] requires Docker and Kubernetes running on your local machine. "
            "[italic]Currently only available on Linux OS.[/italic]"
            "\n\t❕ [purple]existing[/purple] refers to an existing Kubernetes cluster that Nebari can be deployed on.\n"
        )
    )
    inputs.cloud_provider = questionary.select(
        "Where would you like to deploy your Nebari cluster?",
        choices=enum_to_list(ProviderEnum),
        qmark=qmark,
    ).ask()

    if not disable_checks:
        check_cloud_provider_creds(ctx, cloud_provider=inputs.cloud_provider)

    # specific context needed when `check_project_name` is called
    ctx.params["cloud_provider"] = inputs.cloud_provider

    name_guidelines = """
    The project name must adhere to the following requirements:
    - Letters from A to Z (upper and lower case) and numbers
    - Maximum accepted length of the name string is 16 characters
    """
    if inputs.cloud_provider == ProviderEnum.aws.value.lower():
        name_guidelines += "- Should NOT start with the string `aws`\n"
    elif inputs.cloud_provider == ProviderEnum.azure.value.lower():
        name_guidelines += "- Should NOT contain `-`\n"

    # PROJECT NAME
    rich.print(
        (
            f"\n 🪴  Next, give your Nebari instance a project name. This name is what your Kubernetes cluster will be referred to as.\n{name_guidelines}\n\n"
        )
    )
    inputs.project_name = questionary.text(
        "What project name would you like to use?",
        qmark=qmark,
        validate=lambda text: True if len(text) > 0 else "Please enter a value",
    ).ask()

    if not disable_checks:
        check_project_name(ctx, inputs.project_name)

    # DOMAIN NAME
    rich.print(
        (
            "\n 🪴  Great! Now it's time to decide on the domain name (i.e the URL) that Nebari will be accessible from. "
            "This should be a domain that you own.\n\n"
        )
    )
    inputs.domain_name = questionary.text(
        "What domain name would you like to use?",
        qmark=qmark,
        validate=lambda text: True if len(text) > 0 else "Please enter a value",
    ).ask()

    # AUTH PROVIDER
    rich.print(
        (
            "\n 🪴  Nebari comes with [green]Keycloak[/green], an open-source identity and access management tool. This is how users, groups and roles "
            "are managed on the platform. To connect Keycloak with an identity provider, you can select one now.\n\n"
            "\n\t❕ [purple]password[/purple] is the default option and is not connected to any external identity provider.\n"
        )
    )
    inputs.auth_provider = questionary.select(
        "What authentication provider would you like?",
        choices=enum_to_list(AuthenticationEnum),
        qmark=qmark,
    ).ask()

    if not disable_checks:
        check_auth_provider_creds(ctx, auth_provider=inputs.auth_provider)

    if inputs.auth_provider.lower() == AuthenticationEnum.auth0.value.lower():
        inputs.auth_auto_provision = questionary.confirm(
            "Would you like us to auto provision the Auth0 Machine-to-Machine app?",
            default=False,
            qmark=qmark,
        ).ask()

    elif inputs.auth_provider.lower() == AuthenticationEnum.github.value.lower():
        rich.print(
            (
                ":warning: If you haven't done so already, please ensure the following:\n"
                f"The `Homepage URL` is set to: [light_green]https://{inputs.domain_name}[/light_green]\n"
                f"The `Authorization callback URL` is set to: [light_green]https://{inputs.domain_name}/auth/realms/qhub/broker/github/endpoint[/light_green]\n\n"
            )
        )

    # GITOPS - REPOSITORY, CICD
    rich.print(
        (
            "\n 🪴  This next section is [italic]optional[/italic] but recommended. If you wish to adopt a GitOps approach to managing this platform, "
            "we will walk you through a set of questions to get that setup. With this setup, Nebari will use GitHub Actions workflows (or GitLab equivalent) "
            "to automatically handle the future deployments of your infrastructure.\n\n"
        )
    )
    if questionary.confirm(
        "Would you like to adopt a GitOps approach to managing Nebari?",
        default=False,
        qmark=qmark,
    ).ask():

        repo_url = "http://{git_provider}/{org_name}/{repo_name}"

        git_provider = questionary.select(
            "Which git provider would you like to use?",
            choices=["github.com", "gitlab.com"],
            qmark=qmark,
        ).ask()

        org_name = questionary.text(
            f"Which user or organization will this repository live under? ({repo_url.format(git_provider=git_provider, org_name='<org-name>', repo_name='')})",
            qmark=qmark,
        ).ask()

        repo_name = questionary.text(
            f"And what will the name of this repository be? ({repo_url.format(git_provider=git_provider, org_name=org_name, repo_name='<repo-name>')})",
            qmark=qmark,
        ).ask()

        inputs.repository = repo_url.format(
            git_provider=git_provider, org_name=org_name, repo_name=repo_name
        )

        if git_provider == "github.com":
            inputs.repository_auto_provision = questionary.confirm(
                f"Would you like the following git repository to be automatically created: {inputs.repository}?",
                default=False,
                qmark=qmark,
            ).ask()

        # TODO: create `check_repository_creds` function
        if not disable_checks:
            pass

        if git_provider == "github.com":
            inputs.ci_provider = CiEnum.github_actions.value.lower()
        elif git_provider == "gitlab.com":
            inputs.ci_provider = CiEnum.gitlab_ci.value.lower()

    # SSL CERTIFICATE
    rich.print(
        (
            "\n 🪴  This next section is [italic]optional[/italic] but recommended. If you want your Nebari domain to use a Let's Encrypt SSL certificate, "
            "all we need is an email address from you.\n\n"
        )
    )
    ssl_cert = questionary.confirm(
        "Would you like to add a Let's Encrypt SSL certificate to your domain?",
        default=False,
        qmark=qmark,
    ).ask()

    if ssl_cert:
        inputs.ssl_cert_email = questionary.text(
            "Which email address should Let's Encrypt associate the certificate with?",
            qmark=qmark,
        ).ask()

    # ADVANCED FEATURES
    rich.print(
        (
            # TODO once docs are updated, add links for more info on these changes
            "\n 🪴  This next section is [italic]optional[/italic] and includes advanced configuration changes to the "
            "Terraform state, Kubernetes Namespace and Kubernetes version.\n"
            "⚠️ caution is advised!\n\n"
        )
    )
    if questionary.confirm(
        "Would you like to make advanced configuration changes?",
        default=False,
        qmark=qmark,
    ).ask():

        # TERRAFORM STATE
        inputs.terraform_state = questionary.select(
            "Where should the Terraform State be provisioned?",
            choices=enum_to_list(TerraformStateEnum),
            qmark=qmark,
        ).ask()

        # NAMESPACE
        inputs.namespace = questionary.text(
            "What namespace would like to use?",
            default=inputs.namespace,
            qmark=qmark,
        ).ask()

        # KUBERNETES VERSION
        inputs.kubernetes_version = questionary.text(
            "Which Kubernetes version would you like to use?",
            qmark=qmark,
        ).ask()

    handle_init(inputs)

    rich.print(
        (
            "Congratulations, you have generated the all important [purple]nebari-config.yaml[/purple] file 🎉\n\n"
            "You can always edit your [purple]nebari-config.yaml[/purple] file by editing the file directly.\n"
            "If you do make changes to it you can ensure it's still a valid configuration by running:\n\n"
            "\t\t[green]nebari validate --config path/to/nebari-config.yaml[/green]\n\n"
        )
    )

    base_cmd = f"nebari init {inputs.cloud_provider}"

    def if_used(key, model=inputs, ignore_list=["cloud_provider"]):
        if key not in ignore_list:
            b = "--{key} {value}"
            value = getattr(model, key)
            if isinstance(value, str) and (value != "" or value is not None):
                return b.format(key=key, value=value).replace("_", "-")
            if isinstance(value, bool) and value:
                return b.format(key=key, value=value).replace("_", "-")

    cmds = " ".join(
        [_ for _ in [if_used(_) for _ in inputs.dict().keys()] if _ is not None]
    )

    rich.print(
        (
            "For reference, if the previous Guided Init answers were converted into a direct [green]nebari init[/green] command, it would be:\n\n"
            f"\t\t[green]{base_cmd} {cmds}[/green]\n\n"
        )
    )

    raise typer.Exit()
