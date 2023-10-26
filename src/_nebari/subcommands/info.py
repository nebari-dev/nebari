import collections

import rich
import typer
from rich.table import Table

from _nebari.version import __version__
from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command()
    def info(ctx: typer.Context):
        from nebari.plugins import nebari_plugin_manager

        rich.print(f"Nebari version: {__version__}")

        hooks = collections.defaultdict(list)
        for plugin in nebari_plugin_manager.plugin_manager.get_plugins():
            for hook in nebari_plugin_manager.plugin_manager.get_hookcallers(plugin):
                hooks[hook.name].append(plugin.__name__)

        table = Table(title="Hooks")
        table.add_column("hook", justify="left", no_wrap=True)
        table.add_column("module", justify="left", no_wrap=True)

        for hook_name, modules in hooks.items():
            for module in modules:
                table.add_row(hook_name, module)

        rich.print(table)

        table = Table(title="Runtime Stage Ordering")
        table.add_column("name")
        table.add_column("priority")
        table.add_column("module")
        for stage in nebari_plugin_manager.ordered_stages:
            table.add_row(
                stage.name, str(stage.priority), f"{stage.__module__}.{stage.__name__}"
            )

        rich.print(table)
