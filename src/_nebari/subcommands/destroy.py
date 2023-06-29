import pathlib

import typer

from _nebari.config import read_configuration
from _nebari.destroy import destroy_configuration
from _nebari.render import render_template
from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command()
    def destroy(
        ctx: typer.Context,
        config_filename: pathlib.Path = typer.Option(
            ..., "-c", "--config", help="nebari configuration file path"
        ),
        output_directory: pathlib.Path = typer.Option(
            "./",
            "-o",
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
        from nebari.plugins import nebari_plugin_manager

        stages = nebari_plugin_manager.ordered_stages
        config_schema = nebari_plugin_manager.config_schema

        def _run_destroy(
            config_filename=config_filename, disable_render=disable_render
        ):
            config = read_configuration(config_filename, config_schema=config_schema)

            if not disable_render:
                render_template(output_directory, config, stages)

            destroy_configuration(config, stages)

        if disable_prompt:
            _run_destroy()
        elif typer.confirm("Are you sure you want to destroy your Nebari cluster?"):
            _run_destroy()
        else:
            raise typer.Abort()
