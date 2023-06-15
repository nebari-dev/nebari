import importlib
import sys

import pluggy

from nebari import hookspecs

DEFAULT_PLUGINS = [
    # stages
    "_nebari.stages.terraform_state",
    "_nebari.stages.infrastructure",
    "_nebari.stages.kubernetes_initialize",
    "_nebari.stages.kubernetes_ingress",
    "_nebari.stages.kubernetes_keycloak",
    "_nebari.stages.kubernetes_keycloak_configuration",
    "_nebari.stages.kubernetes_services",
    "_nebari.stages.nebari_tf_extensions",
    # subcommands
    "_nebari.subcommands.dev",
    # "_nebari.subcommands.deploy",
    # "_nebari.subcommands.destroy",
    "_nebari.subcommands.keycloak",
    "_nebari.subcommands.render",
    "_nebari.subcommands.support",
    # "_nebari.subcommands.upgrade",
    "_nebari.subcommands.validate",
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
