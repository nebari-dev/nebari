from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import typer
from click import Context
from kubernetes import client
from kubernetes import config as kube_config
from rich import print
from ruamel import yaml
from typer.core import TyperGroup

from qhub.cli._init import (
    check_auth_provider_creds,
    check_cloud_provider_creds,
    check_project_name,
    enum_to_list,
    guided_init_wizard,
    handle_init,
)
from qhub.cli._keycloak import app_keycloak
from qhub.cost import infracost_report
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
from qhub.upgrade import do_upgrade
from qhub.utils import load_yaml
from qhub.version import __version__

SECOND_COMMAND_GROUP_NAME = "Additional Commands"
GUIDED_INIT_MSG = (
    "[bold green]START HERE[/bold green] - this will guide you step-by-step "
    "to generate your [purple]nebari-config.yaml[/purple]. "
    "It is an [i]alternative[/i] to passing the options listed below."
)
KEYCLOAK_COMMAND_MSG = (
    "Interact with the Nebari Keycloak identity and access management tool."
)


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
app.add_typer(
    app_keycloak,
    name="keycloak",
    help=KEYCLOAK_COMMAND_MSG,
    rich_help_panel=SECOND_COMMAND_GROUP_NAME,
)


@app.callback(invoke_without_command=True)
def version(
    version: Optional[bool] = typer.Option(
        None,
        "-v",
        "--version",
        help="Nebari version number",
        is_eager=True,
    ),
):
    if version:
        print(__version__)
        raise typer.Exit()


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
    inputs.disable_prompt = disable_prompt
    # TODO remove when Typer CLI is out of BETA
    inputs.nebari = True

    handle_init(inputs)


@app.command(rich_help_panel=SECOND_COMMAND_GROUP_NAME)
def validate(
    config: str = typer.Option(
        ...,
        "--config",
        "-c",
        help="qhub configuration yaml file path, please pass in as -c/--config flag",
    ),
    enable_commenting: bool = typer.Option(
        False, "--enable_commenting", help="Toggle PR commenting on GitHub Actions"
    ),
):
    """
    Validate the values in the [purple]nebari-config.yaml[/purple] file are acceptable.
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
        ...,
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
    config: str = typer.Option(
        ..., "-c", "--config", help="qhub configuration file path"
    ),
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
    disable_prompt: bool = typer.Option(
        False,
        "--disable-prompt",
        help="Destroy entire Nebari cluster without confirmation request. Suggested for CI use.",
    ),
):
    """
    Destroy the Nebari cluster from your [purple]nebari-config.yaml[/purple] file.
    """
    if not disable_prompt:
        if typer.confirm("Are you sure you want to destroy your Nebari cluster?"):
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


@app.command(rich_help_panel=SECOND_COMMAND_GROUP_NAME)
def cost(
    path: str = typer.Option(
        None,
        "-p",
        "--path",
        help="Pass the path of your stages directory generated after rendering QHub configurations before deployment",
    ),
    dashboard: bool = typer.Option(
        True,
        "-d",
        "--dashboard",
        help="Enable the cost dashboard",
    ),
    file: str = typer.Option(
        None,
        "-f",
        "--file",
        help="Specify the path of the file to store the cost report",
    ),
    currency: str = typer.Option(
        "USD",
        "-c",
        "--currency",
        help="Specify the currency code to use in the cost report",
    ),
    compare: bool = typer.Option(
        False,
        "-cc",
        "--compare",
        help="Compare the cost report to a previously generated report",
    ),
):
    """
    Estimate the cost of deploying Nebari based on your [purple]nebari-config.yaml[/purple]. [italic]Experimental.[/italic]

    [italic]This is still only experimental using Infracost under the hood.
    The estimated value is a base cost and does not include usage costs.[/italic]
    """
    infracost_report(
        path=path,
        dashboard=True,
        file=file,
        currency_code=currency,
        compare=False,
    )


@app.command(rich_help_panel=SECOND_COMMAND_GROUP_NAME)
def upgrade(
    config: str = typer.Option(
        ...,
        "-c",
        "--config",
        help="qhub configuration file path",
    ),
    attempt_fixes: bool = typer.Option(
        False,
        "--attempt-fixes",
        help="Attempt to fix the config for any incompatibilities between your old and new QHub versions.",
    ),
):
    """
    Upgrade your [purple]nebari-config.yaml[/purple] from pre-0.4.0 to 0.4.0.

    Due to several breaking changes that came with the 0.4.0 release, this utility is available to help
    update your [purple]nebari-config.yaml[/purple] to comply with the introduced changes.
    See the project [green]RELEASE.md[/green] for details.
    """
    config_filename = Path(config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    do_upgrade(config_filename, attempt_fixes=attempt_fixes)


@app.command(rich_help_panel=SECOND_COMMAND_GROUP_NAME)
def support(
    config_filename: str = typer.Option(
        ...,
        "-c",
        "--config",
        help="qhub configuration file path",
    ),
    output: str = typer.Option(
        "./qhub-support-logs.zip",
        "-o",
        "--output",
        help="output filename",
    ),
):
    """
    Support tool to write all Kubernetes logs locally and compress them into a zip file.

    The Nebari team recommends k9s to manage and inspect the state of the cluster.
    However, this command occasionally helpful for debugging purposes should the logs need to be shared.
    """

    kube_config.load_kube_config()

    v1 = client.CoreV1Api()

    namespace = get_config_namespace(config=config_filename)

    pods = v1.list_namespaced_pod(namespace=namespace)

    for pod in pods.items:
        Path(f"./log/{namespace}").mkdir(parents=True, exist_ok=True)
        path = Path(f"./log/{namespace}/{pod.metadata.name}.txt")
        with path.open(mode="wt") as file:
            try:
                file.write(
                    "%s\t%s\t%s\n"
                    % (
                        pod.status.pod_ip,
                        namespace,
                        pod.metadata.name,
                    )
                )

                # some pods are running multiple containers
                containers = [
                    _.name if len(pod.spec.containers) > 1 else None
                    for _ in pod.spec.containers
                ]

                for container in containers:
                    if container is not None:
                        file.write(f"Container: {container}\n")
                    file.write(
                        v1.read_namespaced_pod_log(
                            name=pod.metadata.name,
                            namespace=namespace,
                            container=container,
                        )
                    )

            except client.exceptions.ApiException as e:
                file.write("%s not available" % pod.metadata.name)
                raise e

    with ZipFile(output, "w") as zip:
        for file in list(Path(f"./log/{namespace}").glob("*.txt")):
            print(file)
            zip.write(file)


def get_config_namespace(config):
    config_filename = Path(config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    return config["namespace"]


if __name__ == "__main__":
    app()
