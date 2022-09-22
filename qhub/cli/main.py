from pathlib import Path

import rich
import typer
from click import Context
from rich import print
from typer.core import TyperGroup

from qhub.cli._init import (
    check_auth_provider_creds,
    check_cloud_provider_creds,
    check_project_name,
    handle_init,
)
from qhub.deploy import deploy_configuration
from qhub.destroy import destroy_configuration
from qhub.render import render_template
from qhub.schema import (
    AuthenticationEnum,
    CiEnum,
    InitInputs,
    ProviderEnum,
    TerraformStateEnum,
    verify,
)
from qhub.utils import load_yaml


def enum_to_list(enum_cls):
    return [e.value for e in enum_cls]


class OrderCommands(TyperGroup):
    def list_commands(self, ctx: Context):
        """Return list of commands in the order appear."""
        return list(self.commands)


app = typer.Typer(
    cls=OrderCommands,
    help="Nebari CLI 🪴",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command()
def guided_init(
    ctx: typer.Context,
    disable_checks: bool = typer.Option(
        default=False,
    ),
):
    """
    [bold green]START HERE[/bold green] if you're new to Nebari. This is the Guided Init wizard used to create and initialize your [purple]nebari-config.yaml[/purple] file.

    To get started simply run:

            [green]nebari guided-init[/green]

    This command asks a few important questions and when complete, will generate:
    :sparkles: [purple]nebari-config.yaml[/purple], which:
        contains all your Nebari cluster configuration details and,
        is used as input to later commands such as [green]nebari render[/green], [green]nebari deploy[/green], etc.
    :sparkles: [purple].env[/purple], which:
        contains all your important environment variables (i.e. cloud credentials, tokens, etc.) and,
        is only stored on your local machine and used as a convenience.

    [yellow]NOTE[/yellow]
    This CLI command completes the same task, generating the [purple]nebari-config.yaml[/purple], as the generic
    [green]nebari init[/green] command but does so without the need to enter all the flags required to get started.
    """

    rich.print(
        (
            "Welcome to the Guided Init wizard!\n"
            "You will be asked a few questions that are used to generate your [purple]nebari-config.yaml[/purple] and [purple].env[/purple] files.\n\n"
            "For more detail about the [green]nebari init[/green] command, please refer to our docs:\n\n"
            "\t\t[light_green]https://nebari-docs.netlify.app[/light_green]\n\n"
        )
    )

    if disable_checks:
        rich.print(
            "⚠️  Attempting to use the Guided Init wizard without any validation checks. There is no guarantee values provided will work!  ⚠️\n\n"
        )

    import questionary

    qmark = " 🪴 "

    # pull in default values for each of the below
    inputs = InitInputs()

    # CLOUD PROVIDER
    inputs.cloud_provider = questionary.select(
        "Where would you like to deploy your Nebari cluster?",
        choices=enum_to_list(ProviderEnum),
        qmark=qmark,
    ).ask()

    if not disable_checks:
        check_cloud_provider_creds(ctx, cloud_provider=inputs.cloud_provider)

    # specific context needed when `check_project_name` is called
    ctx.params["cloud_provider"] = inputs.cloud_provider

    # PROJECT NAME
    inputs.project_name = questionary.text(
        "What project name would you like to use?",
        qmark=qmark,
        validate=lambda text: True if len(text) > 0 else "Please enter a value",
    ).ask()

    if not disable_checks:
        check_project_name(ctx, inputs.project_name)

    # DOMAIN NAME
    inputs.domain_name = questionary.text(
        "What domain name would you like to use?",
        qmark=qmark,
        validate=lambda text: True if len(text) > 0 else "Please enter a value",
    ).ask()

    # NAMESPACE
    inputs.namespace = questionary.text(
        "What namespace would like to use?",
        default=inputs.namespace,
        qmark=qmark,
    ).ask()

    # AUTH PROVIDER
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

    # REPOSITORY
    if questionary.confirm(
        "Would you like to store this project in a git repo?",
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
            f"Which user or organization will this repo live under? ({repo_url.format(git_provider=git_provider, org_name='<org-name>', repo_name='<repo-name>')})",
            qmark=qmark,
        ).ask()

        repo_name = questionary.text(
            f"And what is the name of this repo? ({repo_url.format(git_provider=git_provider, org_name=org_name, repo_name='<repo-name>')})",
            qmark=qmark,
        ).ask()

        inputs.repository = repo_url.format(
            git_provider=git_provider, org_name=org_name, repo_name=repo_name
        )

        inputs.repository_auto_provision = questionary.confirm(
            f"Would you like us to auto create the following git repo: {inputs.repository}?",
            default=False,
            qmark=qmark,
        ).ask()

        # create `check_repository_creds` function
        if not disable_checks:
            pass

    # CICD
    inputs.ci_provider = questionary.select(
        "Would you like to adopt a GitOps workflow for this repository?",
        choices=enum_to_list(CiEnum),
        qmark=qmark,
    ).ask()

    # SSL CERTIFICATE
    ssl_cert = questionary.confirm(
        "Would you like to add a Let's Encrypt SSL certificate to your cluster?",
        default=False,
        qmark=qmark,
    ).ask()

    if ssl_cert:
        inputs.ssl_cert_email = questionary.text(
            "Which email address should Let's Encrypt associate the certificate with?",
            qmark=qmark,
        ).ask()

    # ADVANCED FEATURES
    if questionary.confirm(
        "Would you like to make advanced configuration changes (⚠️ caution is advised)?",
        default=False,
        qmark=qmark,
    ).ask():

        inputs.terraform_state = questionary.select(
            "Where should the Terraform State be provisioned?",
            choices=enum_to_list(TerraformStateEnum),
            qmark=qmark,
        ).ask()

        inputs.kubernetes_version = questionary.text(
            "Which Kubernetes version would you like to use?",
            qmark=qmark,
        ).ask()

    handle_init(inputs)

    rich.print(
        (
            "Congratulations, you have generated the all important [purple]nebari-config.yaml[/purple] file 🎉\n\n"
            "You can always edit your [purple]nebari-config.yaml[/purple] file by editing the file directly."
            "If you do make changes to you can ensure its still a valid configuration by running:\n\n"
            "\t\t[green]nebari validate --config path/to/nebari-config.yaml[/green]\n\n"
        )
    )

    base_cmd = f"nebari init {inputs.cloud_provider}"

    def if_used(key, model=inputs, ignore_list=["cloud_provider"]):
        if key not in ignore_list:
            b = "--{key} {value}"
            value = getattr(model, key)
            if isinstance(value, str) and value != "":
                return b.format(key=key, value=value).replace("_", "-")
            if isinstance(value, bool) and value:
                return b.format(key=key, value=value).replace("_", "-")

    cmds = " ".join(
        [_ for _ in [if_used(_) for _ in inputs.dict().keys()] if _ is not None]
    )

    rich.print(
        (
            "Here is the previous Guided Init if it was converted into a [green]nebari init[/green] command:\n\n"
            f"\t\t[green]{base_cmd} {cmds}[/green]\n\n"
        )
    )


@app.command()
def init(
    cloud_provider: str = typer.Argument(
        "local",
        help=f"options: {enum_to_list(ProviderEnum)}",
        callback=check_cloud_provider_creds,
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
    auth_provider: str = typer.Option(
        "password",
        help=f"options: {enum_to_list(AuthenticationEnum)}",
        callback=check_auth_provider_creds,
    ),
    auth_auto_provision: bool = typer.Option(
        False,
    ),
    repository: str = typer.Option(
        None,
    ),
    repository_auto_provision: bool = typer.Option(
        False,
    ),
    ci_provider: str = typer.Option(
        None,
        help=f"options: {enum_to_list(CiEnum)}",
    ),
    terraform_state: str = typer.Option(
        "remote", help=f"options: {enum_to_list(TerraformStateEnum)}"
    ),
    kubernetes_version: str = typer.Option(
        "latest",
    ),
    ssl_cert_email: str = typer.Option(
        None,
    ),
):
    """
    Create and initialize your [purple]nebari-config.yaml[/purple] file.
    """
    inputs = InitInputs()

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

    handle_init(inputs)


@app.command()
def validate(
    config: str = typer.Option(
        None,
        "--config",
        "-c",
        help="qhub configuration yaml file path, please pass in as -c/--config flag",
    ),
    enable_commenting: bool = typer.Option(
        False, "--enable_commenting", help="Toggle PR commenting on GitHub Actions"
    ),
):
    """
    Validate the [purple]nebari-config.yaml[/purple] file.
    """
    config_filename = Path(config)
    if not config_filename.is_file():
        raise ValueError(
            f"Passed in configuration filename={config_filename} must exist."
        )

    config = load_yaml(config_filename)

    if enable_commenting:
        # for PR's only
        # comment_on_pr(config)
        pass
    else:
        verify(config)
        print("[bold purple]Successfully validated configuration.[/bold purple]")


@app.command()
def render(
    output: str = typer.Option(
        "./",
        "-o",
        "--output",
        help="output directory",
    ),
    config: str = typer.Option(
        None,
        "-c",
        "--config",
        help="nebari configuration yaml file path",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="simulate rendering files without actually writing or updating any files",
    ),
):
    """
    Dynamically render the Terraform scripts and other files from your [purple]nebari-config.yaml[/purple] file.
    """
    config_filename = Path(config)

    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    config_yaml = load_yaml(config_filename)

    verify(config_yaml)

    render_template(output, config, force=True, dry_run=dry_run)


@app.command()
def deploy(
    config: str = typer.Option(
        ...,
        "--config",
        "-c",
        help="nebari configuration yaml file path",
    ),
    output: str = typer.Option(
        "./",
        "-o",
        "--output",
        help="output directory",
    ),
    dns_provider: str = typer.Option(
        False,
        "--dns-provider",
        help="dns provider to use for registering domain name mapping",
    ),
    dns_auto_provision: bool = typer.Option(
        False,
        "--dns-auto-provision",
        help="Attempt to automatically provision DNS. For Auth0 is requires environment variables AUTH0_DOMAIN, AUTH0_CLIENTID, AUTH0_CLIENT_SECRET",
    ),
    disable_prompt: bool = typer.Option(
        False,
        "--disable-prompt",
        help="Disable human intervention",
    ),
    disable_render: bool = typer.Option(
        False,
        "--disable-render",
        help="Disable auto-rendering in deploy stage",
    ),
):
    """
    Deploy the Nebari cluster from your [purple]nebari-config.yaml[/purple] file.
    """
    config_filename = Path(config)

    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    config_yaml = load_yaml(config_filename)

    verify(config_yaml)

    if not disable_render:
        render_template(output, config, force=True)

    deploy_configuration(
        config_yaml,
        dns_provider=dns_provider,
        dns_auto_provision=dns_auto_provision,
        disable_prompt=disable_prompt,
        disable_checks=False,
        skip_remote_state_provision=False,
    )


@app.command()
def destroy(
    config: str = typer.Option(..., "-c", "--config", help="qhub configuration"),
    output: str = typer.Option(
        "./" "-o",
        "--output",
        help="output directory",
    ),
    disable_render: bool = typer.Option(
        False,
        "--disable-render",
        help="Disable auto-rendering before destroy",
    ),
):
    """
    Destroy the Nebari cluster from your [purple]nebari-config.yaml[/purple] file.
    """
    delete = typer.confirm("Are you sure you want to destroy it?")
    if not delete:
        raise typer.Abort()
    else:
        config_filename = Path(config)
        if not config_filename.is_file():
            raise ValueError(
                f"passed in configuration filename={config_filename} must exist"
            )

        config_yaml = load_yaml(config_filename)

        verify(config_yaml)

        if not disable_render:
            render_template(output, config, force=True)

        destroy_configuration(config_yaml)


if __name__ == "__main__":
    app()
