import pathlib

import typer

from _nebari.destroy import destroy_configuration
from _nebari.render import render_template
from _nebari.utils import load_yaml
from nebari import schema
from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @app.command()
    def destroy(
        config: str = typer.Option(
            ..., "-c", "--config", help="nebari configuration file path"
        ),
        output: str = typer.Option(
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

        def _run_destroy(config=config, disable_render=disable_render):
            config_filename = pathlib.Path(config)
            if not config_filename.is_file():
                raise ValueError(
                    f"passed in configuration filename={config_filename} must exist"
                )

            config_yaml = load_yaml(config_filename)

            schema.verify(config_yaml)

            if not disable_render:
                render_template(output, config)

            destroy_configuration(config_yaml)

        if disable_prompt:
            _run_destroy()
        elif typer.confirm("Are you sure you want to destroy your Nebari cluster?"):
            _run_destroy()
        else:
            raise typer.Abort()
