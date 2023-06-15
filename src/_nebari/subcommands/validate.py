import pathlib

import typer

from _nebari.utils import load_yaml
from nebari import schema
from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command(rich_help_panel="Additional Commands")
    def validate(
        config: str = typer.Option(
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
            schema.verify(config)
            print("[bold purple]Successfully validated configuration.[/bold purple]")
