import pathlib

import typer

from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command(rich_help_panel="Additional Commands")
    def render(
        ctx: typer.Context,
        output_directory: pathlib.Path = typer.Option(
            "./",
            "-o",
            "--output",
            help="output directory",
        ),
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

        nebari_plugin_manager.read_configuration(config_filename)
        nebari_plugin_manager.render_stages(
            template_directory=output_directory, dry_run=dry_run
        )
