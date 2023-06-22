import importlib
import typing
import pathlib
import sys
import os

import typer
from typer.core import TyperGroup

from _nebari.version import __version__
from nebari import schema
from nebari.plugins import pm, load_plugins


class OrderCommands(TyperGroup):
    def list_commands(self, ctx: typer.Context):
        """Return list of commands in the order appear."""
        return list(self.commands)


def version_callback(value: bool):
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def exclude_stages(ctx: typer.Context, stages: typing.List[str]):
    ctx.ensure_object(schema.CLIContext)
    ctx.obj.excluded_stages = stages
    return stages


def exclude_default_stages(ctx: typer.Context, exclude_default_stages: bool):
    ctx.ensure_object(schema.CLIContext)
    ctx.obj.exclude_default_stages = exclude_default_stages
    return exclude_default_stages


def import_plugin(plugins: typing.List[str]):
    try:
        load_plugins(plugins)
    except ModuleNotFoundError as e:
        typer.echo("ERROR: Python module {e.name} not found. Make sure that the module is in your python path {sys.path}")
        typer.Exit()
    return plugins


def create_cli():
    app = typer.Typer(
        cls=OrderCommands,
        help="Nebari CLI 🪴",
        add_completion=False,
        no_args_is_help=True,
        rich_markup_mode="rich",
        pretty_exceptions_show_locals=False,
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @app.callback()
    def common(
        ctx: typer.Context,
        version: bool = typer.Option(
            None,
            "-V",
            "--version",
            help="Nebari version number",
            callback=version_callback,
        ),
        plugins: typing.List[str] = typer.Option(
            [], "--import-plugin", help="Import nebari plugin",
        ),
        excluded_stages: typing.List[str] = typer.Option(
            [], "--exclude-stage", help="Exclude nebari stage(s) by name or regex",
        ),
        exclude_default_stages: bool = typer.Option(
            False, '--exclude-default-stages', help="Exclude default nebari included stages",
        )
    ):
        try:
            load_plugins(plugins)
        except ModuleNotFoundError as e:
            typer.echo("ERROR: Python module {e.name} not found. Make sure that the module is in your python path {sys.path}")
            typer.Exit()

        from _nebari.stages.base import get_available_stages
        ctx.ensure_object(schema.CLIContext)
        ctx.obj.stages = get_available_stages(
            exclude_default_stages=exclude_default_stages,
            exclude_stages=excluded_stages
        )


    pm.hook.nebari_subcommand(cli=app)

    return app
