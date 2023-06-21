import importlib
import itertools
import sys

import pluggy
from pydantic import BaseModel
from pydantic.main import create_model

from nebari import hookspecs

DEFAULT_PLUGINS = [
    # stages
    "_nebari.stages.bootstrap",
    "_nebari.stages.terraform_state",
    "_nebari.stages.infrastructure",
    "_nebari.stages.kubernetes_initialize",
    "_nebari.stages.kubernetes_ingress",
    "_nebari.stages.kubernetes_keycloak",
    "_nebari.stages.kubernetes_keycloak_configuration",
    "_nebari.stages.kubernetes_services",
    "_nebari.stages.nebari_tf_extensions",
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
]

pm = pluggy.PluginManager("nebari")
pm.add_hookspecs(hookspecs)


def get_available_stages() -> list:
    stages = itertools.chain.from_iterable(pm.hook.nebari_stage())

    # order stages by priority
    sorted_stages = sorted(stages, key=lambda s: s.priority)

    # filter out duplicate stages with same name (keep highest priority)
    visited_stage_names = set()
    filtered_stages = []
    for stage in reversed(sorted_stages):
        if stage.name in visited_stage_names:
            continue
        filtered_stages.insert(0, stage)
        visited_stage_names.add(stage.name)

    return filtered_stages


def create_dynamic_schema(
    plugin: BaseModel, base: BaseModel, model_name: str = "ExtendedConfig"
) -> BaseModel:
    extra_fields = {}
    for n, f in plugin.__fields__.items():
        extra_fields[n] = (f.type_, f.default if f.default is not None else ...)
    return create_model(model_name, __base__=base, **extra_fields)


def extend_schema(base_schema: BaseModel) -> BaseModel:
    config = None
    for stages in get_available_stages():
        if stages.stage_schema:
            config = create_dynamic_schema(stages.stage_schema, base_schema)

    if config:
        return config
    return base_schema


if not hasattr(sys, "_called_from_test"):
    # Only load plugins if not running tests
    pm.load_setuptools_entrypoints("nebari")

# Load default plugins
for plugin in DEFAULT_PLUGINS:
    mod = importlib.import_module(plugin)
    pm.register(mod, plugin)
