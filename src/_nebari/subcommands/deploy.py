import pathlib
from typing import Optional

import rich
import typer

from _nebari.config import read_configuration
from _nebari.deploy import deploy_configuration
from _nebari.render import render_template
from nebari.hookspecs import hookimpl

TERRAFORM_STATE_STAGE_NAME = "01-terraform-state"


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command()
    def deploy(
        ctx: typer.Context,
        config_filename: pathlib.Path = typer.Option(
            ...,
            "--config",
            "-c",
            help="nebari configuration yaml file path",
        ),
        output_directory: pathlib.Path = typer.Option(
            "./",
            "-o",
            "--output",
            help="output directory",
        ),
        dns_provider: Optional[str] = typer.Option(
            None,
            "--dns-provider",
            help="dns provider to use for registering domain name mapping ⚠️ moved to `dns.provider` in nebari-config.yaml",
        ),
        dns_auto_provision: bool = typer.Option(
            False,
            "--dns-auto-provision",
            help="Attempt to automatically provision DNS, currently only available for `cloudflare` ⚠️ moved to `dns.auto_provision` in nebari-config.yaml",
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
        from nebari.plugins import nebari_plugin_manager

        if dns_provider or dns_auto_provision:
            msg = "The [green]`--dns-provider`[/green] and [green]`--dns-auto-provision`[/green] flags have been removed in favor of configuring DNS via nebari-config.yaml"
            rich.print(msg)
            raise typer.Abort()

        stages = nebari_plugin_manager.ordered_stages
        config_schema = nebari_plugin_manager.config_schema

        config = read_configuration(config_filename, config_schema=config_schema)

        if not disable_render:
            render_template(output_directory, config, stages)

        if skip_remote_state_provision:
            for stage in stages:
                if stage.name == TERRAFORM_STATE_STAGE_NAME:
                    stages.remove(stage)
            rich.print("Skipping remote state provision")

        # Digital Ocean support deprecation warning -- Nebari 2024.7.1
        if config.provider == "do" and not disable_prompt:
            msg = "Digital Ocean support is currently being deprecated and will be removed in a future release. Would you like to continue?"
            typer.confirm(msg)

        deploy_configuration(
            config,
            stages,
            disable_prompt=disable_prompt,
            disable_checks=disable_checks,
        )
