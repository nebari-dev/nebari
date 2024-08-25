import itertools
import os
import re
import sys
import typing
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pluggy

from nebari import hookspecs, schema

DEFAULT_SUBCOMMAND_PLUGINS = [
    # subcommands
    "_nebari.subcommands.info",
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

DEFAULT_STAGES_PLUGINS = [
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
    "_nebari.stages.kubernetes_kuberhealthy",
    "_nebari.stages.kubernetes_kuberhealthy_healthchecks",
]


class NebariPluginManager:
    plugin_manager = pluggy.PluginManager("nebari")

    exclude_default_stages: bool = False
    exclude_stages: typing.List[str] = []

    def __init__(self) -> None:
        self.plugin_manager.add_hookspecs(hookspecs)

        if not hasattr(sys, "_called_from_test"):
            # Only load plugins if not running tests
            self.plugin_manager.load_setuptools_entrypoints("nebari")

        self.load_plugins(DEFAULT_SUBCOMMAND_PLUGINS)

    def load_plugins(self, plugins: typing.List[str]):
        def _import_module_from_filename(plugin: str):
            module_name = f"_nebari.stages._files.{plugin.replace(os.sep, '.')}"
            spec = spec_from_file_location(module_name, plugin)
            if spec is None:
                raise ImportError(f"Can not find {plugin!r} plugin.")
            if spec.loader is None:
                raise ImportError(f"Can not load {plugin!r} plugin.")
            module = module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module

        for plugin in plugins:
            if plugin.endswith(".py"):
                mod = _import_module_from_filename(plugin)
            else:
                mod = import_module(plugin)

            try:
                self.plugin_manager.register(mod, plugin)
            except ValueError:
                # Plugin already registered
                pass

    def get_available_stages(self):
        if not self.exclude_default_stages:
            self.load_plugins(DEFAULT_STAGES_PLUGINS)

        stages = itertools.chain.from_iterable(self.plugin_manager.hook.nebari_stage())

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

        # filter out stages which match excluded stages
        included_stages = []
        for stage in filtered_stages:
            for exclude_stage in self.exclude_stages:
                if re.fullmatch(exclude_stage, stage.name) is not None:
                    break
            else:
                included_stages.append(stage)

        return included_stages

    def read_config(self, config_path: typing.Union[str, Path], **kwargs):
        if isinstance(config_path, str):
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file {config_path} not found")

        from _nebari.config import read_configuration

        return read_configuration(config_path, self.config_schema, **kwargs)

    @property
    def ordered_stages(self):
        return self.get_available_stages()

    @property
    def config_schema(self):
        classes = [schema.Main] + [
            _.input_schema for _ in self.ordered_stages if _.input_schema is not None
        ]
        return type("ConfigSchema", tuple(classes[::-1]), {})


nebari_plugin_manager = NebariPluginManager()
