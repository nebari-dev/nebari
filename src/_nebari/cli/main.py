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

from _nebari.cli.dev import app_dev
from _nebari.cli.init import (
    check_auth_provider_creds,
    check_cloud_provider_creds,
    check_project_name,
    check_ssl_cert_email,
    enum_to_list,
    guided_init_wizard,
    handle_init,
)
from _nebari.cli.keycloak import app_keycloak
from _nebari.deploy import deploy_configuration
from _nebari.destroy import destroy_configuration
from _nebari.render import render_template
from _nebari.schema import (
    AuthenticationEnum,
    CiEnum,
    GitRepoEnum,
    InitInputs,
    ProviderEnum,
    TerraformStateEnum,
    verify,
)
from _nebari.upgrade import do_upgrade
from _nebari.utils import load_yaml
from _nebari.version import __version__

SECOND_COMMAND_GROUP_NAME = "Additional Commands"
GUIDED_INIT_MSG = (
    "[bold green]START HERE[/bold green] - this will guide you step-by-step "
    "to generate your [purple]nebari-config.yaml[/purple]. "
    "It is an [i]alternative[/i] to passing the options listed below."
)
KEYCLOAK_COMMAND_MSG = (
    "Interact with the Nebari Keycloak identity and access management tool."
)
DEV_COMMAND_MSG = "Development tools and advanced features."


def path_callback(value: str) -> Path:
    return Path(value).expanduser().resolve()


def config_path_callback(value: str) -> Path:
    value = path_callback(value)
    if not value.is_file():
        raise ValueError(f"Passed configuration path {value} does not exist!")
    return value


CONFIG_PATH_OPTION: Path = typer.Option(
    ...,
    "--config",
    "-c",
    help="nebari configuration yaml file path, please pass in as -c/--config flag",
    callback=config_path_callback,
)

OUTPUT_PATH_OPTION: Path = typer.Option(
    Path.cwd(),
    "-o",
    "--output",
    help="output directory",
    callback=path_callback,
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
app.add_typer(
    app_dev,
    name="dev",
    help=DEV_COMMAND_MSG,
    rich_help_panel=SECOND_COMMAND_GROUP_NAME,
)


@app.callback(invoke_without_command=True)
def version(
    version: Optional[bool] = typer.Option(
        None,
        "-V",
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
        help=f"options: {enum_to_list(GitRepoEnum)}",
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

    handle_init(inputs)


@app.command(rich_help_panel=SECOND_COMMAND_GROUP_NAME)
def validate(
    config_path=CONFIG_PATH_OPTION,
    enable_commenting: bool = typer.Option(
        False, "--enable-commenting", help="Toggle PR commenting on GitHub Actions"
    ),
):
    """
    Validate the values in the [purple]nebari-config.yaml[/purple] file are acceptable.
    """
    config = load_yaml(config_path)

    if enable_commenting:
        # for PR's only
        # comment_on_pr(config)
        pass
    else:
        verify(config)
        print("[bold purple]Successfully validated configuration.[/bold purple]")


@app.command(rich_help_panel=SECOND_COMMAND_GROUP_NAME)
def render(
    output_path=OUTPUT_PATH_OPTION,
    config_path=CONFIG_PATH_OPTION,
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="simulate rendering files without actually writing or updating any files",
    ),
):
    """
    Dynamically render the Terraform scripts and other files from your [purple]nebari-config.yaml[/purple] file.
    """
    config = load_yaml(config_path)

    verify(config)

    render_template(output_path, config_path, dry_run=dry_run)


@app.command()
def deploy(
    config_path=CONFIG_PATH_OPTION,
    output_path=OUTPUT_PATH_OPTION,
    dns_provider: str = typer.Option(
        False,
        "--dns-provider",
        help="dns provider to use for registering domain name mapping",
    ),
    dns_auto_provision: bool = typer.Option(
        False,
        "--dns-auto-provision",
        help="Attempt to automatically provision DNS, currently only available for `cloudflare`",
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
    disable_checks: bool = typer.Option(
        False,
        "--disable-checks",
        help="Disable the checks performed after each stage",
    ),
    skip_remote_state_provision: bool = typer.Option(
        False,
        "--skip-remote-state-provision",
        help="Skip terraform state deployment which is often required in CI once the terraform remote state bootstrapping phase is complete",
    ),
):
    """
    Deploy the Nebari cluster from your [purple]nebari-config.yaml[/purple] file.
    """
    config = load_yaml(config_path)

    verify(config)

    if not disable_render:
        render_template(output_path, config_path)

    deploy_configuration(
        config,
        dns_provider=dns_provider,
        dns_auto_provision=dns_auto_provision,
        disable_prompt=disable_prompt,
        disable_checks=disable_checks,
        skip_remote_state_provision=skip_remote_state_provision,
    )


@app.command()
def destroy(
    config_path=CONFIG_PATH_OPTION,
    output_path=OUTPUT_PATH_OPTION,
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

    def _run_destroy(config_path=config_path, disable_render=disable_render):
        config = load_yaml(config_path)

        verify(config)

        if not disable_render:
            render_template(output_path, config_path)

        destroy_configuration(config)

    if disable_prompt:
        _run_destroy()
    elif typer.confirm("Are you sure you want to destroy your Nebari cluster?"):
        _run_destroy()
    else:
        raise typer.Abort()


@app.command(rich_help_panel=SECOND_COMMAND_GROUP_NAME)
def upgrade(
    config_path=CONFIG_PATH_OPTION,
    attempt_fixes: bool = typer.Option(
        False,
        "--attempt-fixes",
        help="Attempt to fix the config for any incompatibilities between your old and new Nebari versions.",
    ),
):
    """
    Upgrade your [purple]nebari-config.yaml[/purple].

    Upgrade your [purple]nebari-config.yaml[/purple] after an nebari upgrade. If necessary, prompts users to perform manual upgrade steps required for the deploy process.

    See the project [green]RELEASE.md[/green] for details.
    """
    do_upgrade(config_path, attempt_fixes=attempt_fixes)


@app.command(rich_help_panel=SECOND_COMMAND_GROUP_NAME)
def support(
    config_path=CONFIG_PATH_OPTION,
    output_path=OUTPUT_PATH_OPTION,
):
    """
    Support tool to write all Kubernetes logs locally and compress them into a zip file.

    The Nebari team recommends k9s to manage and inspect the state of the cluster.
    However, this command occasionally helpful for debugging purposes should the logs need to be shared.
    """
    kube_config.load_kube_config()

    v1 = client.CoreV1Api()

    namespace = get_config_namespace(config_path)

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

    with ZipFile(output_path, "w") as zip:
        for file in list(Path(f"./log/{namespace}").glob("*.txt")):
            print(file)
            zip.write(file)


def get_config_namespace(config_path):
    with open(config_path) as f:
        config = yaml.safe_load(f.read())

    return config["namespace"]


if __name__ == "__main__":
    app()
