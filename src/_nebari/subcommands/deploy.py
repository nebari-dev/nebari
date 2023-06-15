import pathlib

import typer

from _nebari.deploy import deploy_configuration
from _nebari.render import render_template
from _nebari.utils import load_yaml
from nebari import schema
from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command()
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
        config_filename = pathlib.Path(config)

        if not config_filename.is_file():
            raise ValueError(
                f"passed in configuration filename={config_filename} must exist"
            )

        config_yaml = load_yaml(config_filename)

        schema.verify(config_yaml)

        if not disable_render:
            render_template(output, config)

        deploy_configuration(
            config_yaml,
            dns_provider=dns_provider,
            dns_auto_provision=dns_auto_provision,
            disable_prompt=disable_prompt,
            disable_checks=disable_checks,
            skip_remote_state_provision=skip_remote_state_provision,
        )
