from typing import Optional
import importlib

import typer
from typer.core import TyperGroup

from _nebari.version import __version__
from nebari.plugins import pm


class OrderCommands(TyperGroup):
    def list_commands(self, ctx: typer.Context):
        """Return list of commands in the order appear."""
        return list(self.commands)


def version_callback(value: bool):
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def import_module(module: str):
    importlib.__import__(module)


def create_cli():
    app = typer.Typer(
        cls=OrderCommands,
        help="Nebari CLI 🪴",
        add_completion=False,
        no_args_is_help=True,
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @app.callback(invoke_without_command=True)
    def common(
        ctx: typer.Context,
        version: bool = typer.Option(None, "-V", "--version", help="Nebari version number", callback=version_callback),
        import_module: str = typer.Option(None, "--import-module", help="Import nebari module", callback=import_module),
    ):
        pass

    pm.hook.nebari_subcommand(cli=app)

    return app
