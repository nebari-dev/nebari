from pathlib import Path

import typer
from click import Context
from rich import print
from typer.core import TyperGroup

from qhub.cli._init import (
    check_auth_provider_creds,
    check_cloud_provider_creds,
    check_project_name,
    enum_to_list,
    guided_init_wizard,
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

SECOND_COMMAND_GROUP_NAME = "Additional Commands"


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


guided_init_help_msg = (
    "[bold green]START HERE[/bold green] - this will gently guide you through a list of questions "
    "to generate your [purple]nebari-config.yaml[/purple]. "
    "It is an [i]alternative[/i] to passing the options listed below."
)


@app.command()
def init(
    cloud_provider: str = typer.Argument(
        "local",
        help=f"options: {enum_to_list(ProviderEnum)}",
        callback=check_cloud_provider_creds,
        is_eager=True,
    ),
    guided_init: bool = typer.Option(
        False,
        help=guided_init_help_msg,
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

    This command will create and initialize your [purple]nebari-config.yaml[/purple] :sparkles:

    This file contains all your Nebari cluster configuration details and,
    is used as input to later commands such as [green]nebari render[/green], [green]nebari deploy[/green], etc.

    If you're new to Nebari, we recommend you use the Guided Init wizard.
    To get started simply run:

            [green]nebari init --guided-init[/green]

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


@app.command(rich_help_panel=SECOND_COMMAND_GROUP_NAME)
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


@app.command(rich_help_panel=SECOND_COMMAND_GROUP_NAME)
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
