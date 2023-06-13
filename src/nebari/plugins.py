import sys

import pluggy

from nebari import hookspecs

DEFAULT_PLUGINS = [
    "_nebari.stage.kubernetes_initialize_20",
]

pm = pluggy.PluginManager("nebari")
pm.add_hookspecs(hookspecs)

if not hasattr(sys, "_called_from_test"):
    # Only load plugins if not running tests
    pm.load_setuptools_entrypoints("datasette")

# Load default plugins
for plugin in DEFAULT_PLUGINS:
    mod = importlib.import_module(plugin)
    pm.register(mod, plugin)
