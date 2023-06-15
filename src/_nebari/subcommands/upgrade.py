import pathlib

import typer

from nebari.hookspecs import hookimpl
from nebari import schema
from _nebari.utils import load_yaml
from _nebari.upgrade import do_upgrade


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command(rich_help_panel="Additional Commands")
    def upgrade(
        config: str = typer.Option(
            ...,
            "-c",
            "--config",
            help="nebari configuration file path",
        ),
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
        config_filename = pathlib.Path(config)
        if not config_filename.is_file():
            raise ValueError(
                f"passed in configuration filename={config_filename} must exist"
            )

        do_upgrade(config_filename, attempt_fixes=attempt_fixes)
