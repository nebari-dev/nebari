import pathlib

import typer
from rich import print

from nebari import schema
from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command(rich_help_panel="Additional Commands")
    def validate(
        config_filename: pathlib.Path = typer.Option(
            ...,
            "--config",
            "-c",
            help="nebari configuration yaml file path, please pass in as -c/--config flag",
        ),
        enable_commenting: bool = typer.Option(
            False, "--enable-commenting", help="Toggle PR commenting on GitHub Actions"
        ),
    ):
        """
        Validate the values in the [purple]nebari-config.yaml[/purple] file are acceptable.
        """
        if enable_commenting:
            # for PR's only
            # comment_on_pr(config)
            pass
        else:
            from nebari.plugins import nebari_plugin_manager

            config_schema = nebari_plugin_manager.config_schema

            schema.read_configuration(config_filename, config_schema=config_schema)
            print("[bold purple]Successfully validated configuration.[/bold purple]")
