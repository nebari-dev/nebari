import pathlib

import typer
from click import Context
from typer.core import TyperGroup

from qhub.cli._init import check_cloud_provider_creds
from qhub.render import render_template
from qhub.schema import ProviderEnum, verify
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
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command()
def init(
    cloud_provider: str = typer.Argument(
        ...,
        help=f"options: {enum_to_list(ProviderEnum)}",
        callback=check_cloud_provider_creds,
    ),
    project_name: str = typer.Option(
        None,
        "--project-name",
        "--project",
        prompt=True,
        # callback=project_name_convention
    ),
    domain_name: str = typer.Option(
        None,
        "--domain-name",
        "--domain",
        prompt=True,
    ),
    auth_provider: str = typer.Option(
        "password",
        prompt=True,
        # callback=auth_provider_options
    ),
    namespace: str = typer.Option(
        "dev",
        prompt=True,
        # callback=auth_provider_options
    ),
    repository: str = typer.Option(
        None,
        prompt=True,
        # callback=auth_provider_options
    ),
    ci_provider: str = typer.Option(
        "github-actions",
        prompt=True,
        # callback=auth_provider_options
    ),
    terraform_state: str = typer.Option(
        "remote",
        prompt=True,
        # callback=auth_provider_options
    ),
    kubernetes_version: str = typer.Option(
        "latest",
        prompt=True,
        # callback=auth_provider_options
    ),
    ssl_cert: str = typer.Option(
        "email",
        prompt=True,
        # callback=auth_provider_options
    ),
):
    """
    Initialize nebari-config.yaml file.

    """


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
    Validate the config.yaml file.

    """
    # print(f"Validate the {config}")

    config_filename = pathlib.Path(config)
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
        print("Successfully validated configuration")


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
        help="qhub configuration yaml file",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="simulate rendering files without actually writing or updating any files",
    )
    # TODO: debug why dry-run is not working?
):
    """
    Dynamically render terraform scripts and other files from the nebari-config.yaml
    """
    config_filename = pathlib.Path(config)

    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    config_yaml = load_yaml(config_filename)

    verify(config_yaml)

    render_template(output, config, force=True, dry_run=dry_run)


@app.command()
def deploy():
    """
    Deploy the nebari
    """
    print("Deploy the Nebari")


@app.command()
def destroy():
    """
    Destroy the nebari
    """
    print("Destroy the Nebari")


if __name__ == "__main__":
    app()
