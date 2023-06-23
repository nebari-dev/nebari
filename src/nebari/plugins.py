import importlib
import os
import sys
import typing

import pluggy

from nebari import hookspecs

DEFAULT_SUBCOMMAND_PLUGINS = [
    # subcommands
    "_nebari.subcommands.init",
    "_nebari.subcommands.dev",
    "_nebari.subcommands.deploy",
    "_nebari.subcommands.destroy",
    "_nebari.subcommands.keycloak",
    "_nebari.subcommands.render",
    "_nebari.subcommands.support",
    "_nebari.subcommands.upgrade",
    "_nebari.subcommands.validate",
    "_nebari.subcommands.info",
]

pm = pluggy.PluginManager("nebari")
pm.add_hookspecs(hookspecs)

if not hasattr(sys, "_called_from_test"):
    # Only load plugins if not running tests
    pm.load_setuptools_entrypoints("nebari")


# Load default plugins
def load_plugins(plugins: typing.List[str]):
    def _import_module_from_filename(filename: str):
        module_name = f"_nebari.stages._files.{plugin.replace(os.sep, '.')}"
        spec = importlib.util.spec_from_file_location(module_name, plugin)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        return mod

    for plugin in plugins:
        if plugin.endswith(".py"):
            mod = _import_module_from_filename(plugin)
        else:
            mod = importlib.import_module(plugin)

        try:
            pm.register(mod, plugin)
        except ValueError:
            # Pluin already registered
            pass


load_plugins(DEFAULT_SUBCOMMAND_PLUGINS)
