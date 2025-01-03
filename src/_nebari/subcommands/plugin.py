from importlib.metadata import version

import rich
import typer
from rich.table import Table

from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    plugin_cmd = typer.Typer(
        add_completion=False,
        no_args_is_help=True,
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    cli.add_typer(
        plugin_cmd,
        name="plugin",
        help="Interact with nebari plugins",
        rich_help_panel="Additional Commands",
    )

    @plugin_cmd.command()
    def list(ctx: typer.Context):
        """
        List installed plugins
        """
        from nebari.plugins import nebari_plugin_manager

        external_plugins = nebari_plugin_manager.get_external_plugins()

        table = Table(title="Plugins")
        table.add_column("name", justify="left", no_wrap=True)
        table.add_column("version", justify="left", no_wrap=True)

        for plugin in external_plugins:
            table.add_row(plugin, version(plugin))

        rich.print(table)
