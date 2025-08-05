import pathlib

import typer

from _nebari.config import read_configuration
from _nebari.render import render_template
from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command(rich_help_panel="Additional Commands")
    def render(
        ctx: typer.Context,
        # TODO: Remove -o/--output argument until it is safe to use
        # See: https://github.com/nebari-dev/nebari/issues/1716
        # output_directory: pathlib.Path = typer.Option(
        #     "./",
        #     "-o",
        #     "--output",
        #     help="output directory",
        # ),
        config_filename: pathlib.Path = typer.Option(
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
        from nebari.plugins import nebari_plugin_manager

        stages = nebari_plugin_manager.ordered_stages
        config_schema = nebari_plugin_manager.config_schema

        config = read_configuration(config_filename, config_schema=config_schema)
        # Use hardcoded "./" since output_directory parameter was removed
        render_template("./", config, stages, dry_run=dry_run)
