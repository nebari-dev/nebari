from typing import Optional

import typer
from typer.core import TyperGroup

from _nebari.version import __version__
from nebari.plugins import pm


class OrderCommands(TyperGroup):
    def list_commands(self, ctx: typer.Context):
        """Return list of commands in the order appear."""
        return list(self.commands)


def create_cli():
    app = typer.Typer(
        cls=OrderCommands,
        help="Nebari CLI 🪴",
        add_completion=False,
        no_args_is_help=True,
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    pm.hook.nebari_subcommand(cli=app)

    @app.callback(invoke_without_command=True)
    def version(
        version: Optional[bool] = typer.Option(
            None,
            "-V",
            "--version",
            help="Nebari version number",
            is_eager=True,
        ),
    ):
        if version:
            print(__version__)
            raise typer.Exit()

    return app
