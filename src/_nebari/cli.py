import logging
import os
import typing

import typer
from typer.core import TyperGroup

from _nebari.version import __version__
from nebari.plugins import nebari_plugin_manager


class OrderCommands(TyperGroup):
    def list_commands(self, ctx: typer.Context):
        """Return list of commands in the order appear."""
        return list(self.commands)[::-1]


def version_callback(value: bool):
    if value:
        typer.echo(__version__)
        raise typer.Exit()


def exclude_stages(ctx: typer.Context, stages: typing.List[str]):
    nebari_plugin_manager.excluded_stages = stages
    return stages


def exclude_default_stages(ctx: typer.Context, exclude_default_stages: bool):
    nebari_plugin_manager.exclude_default_stages = exclude_default_stages
    return exclude_default_stages


def configure_logging(log_level: None | str) -> None:
    """Configure logging level based on log level string."""
    if not log_level:
        return

    level_map = {
        "trace": logging.DEBUG,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    # Map Python logging levels to Terraform log levels
    tf_log_map = {
        "trace": "TRACE",
        "debug": "DEBUG",
        "info": "INFO",
        "warning": "WARN",
        "error": "ERROR",
        "critical": "ERROR",
    }

    level = level_map.get(log_level.lower(), logging.WARNING)

    # Set TF_LOG environment variable if not already set
    if "TF_LOG" not in os.environ:
        os.environ["TF_LOG"] = tf_log_map.get(log_level.lower(), "WARN")

    if level == logging.DEBUG:
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            force=True,
        )
    else:
        logging.basicConfig(
            level=level, format="%(levelname)s - %(message)s", force=True
        )
    return


def import_plugin(plugins: typing.List[str]):
    try:
        nebari_plugin_manager.load_plugins(plugins)
    except ModuleNotFoundError:
        typer.echo(
            "ERROR: Python module {e.name} not found. Make sure that the module is in your python path {sys.path}"
        )
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
        log_level: str = typer.Option(
            None,
            "-l",
            "--log-level",
            help="Set logging level (trace, debug, info, warning, error, critical)",
            callback=configure_logging,
        ),
        plugins: typing.List[str] = typer.Option(
            [],
            "--import-plugin",
            help="Import nebari plugin",
            callback=import_plugin,
        ),
        excluded_stages: typing.List[str] = typer.Option(
            [],
            "--exclude-stage",
            help="Exclude nebari stage(s) by name or regex",
        ),
        exclude_default_stages: bool = typer.Option(
            False,
            "--exclude-default-stages",
            help="Exclude default nebari included stages",
        ),
    ):
        pass

    nebari_plugin_manager.plugin_manager.hook.nebari_subcommand(cli=app)

    return app
