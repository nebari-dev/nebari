import importlib
import itertools
import os
import shutil
import sys
import typing
from pathlib import Path

import networkx as nx
import pluggy
import pydantic
from ruamel.yaml import YAML

from _nebari.deprecate import DEPRECATED_FILE_PATHS
from _nebari.utils import inspect_files, print_rendered_files
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
]


class NebariPluginManager:
    plugin_manager = pluggy.PluginManager("nebari")

    exclude_default_stages: bool = False
    exclude_stages: typing.List[str] = []

    config_path: typing.Union[Path, None] = None
    config: typing.Union[pydantic.BaseModel, None] = None

    template_directory: typing.Union[Path, None] = None

    _ignore_filenames = (
        [
            "terraform.tfstate",
            ".terraform.lock.hcl",
            "terraform.tfstate.backup",
        ],
    )
    _ignore_directories = (
        [
            ".terraform",
            "__pycache__",
        ],
    )
    _deleted_paths = DEPRECATED_FILE_PATHS

    def __init__(self) -> None:
        self.plugin_manager.add_hookspecs(hookspecs)

        if not hasattr(sys, "_called_from_test"):
            # Only load plugins if not running tests
            self.plugin_manager.load_setuptools_entrypoints("nebari")

        self.load_plugins(DEFAULT_SUBCOMMAND_PLUGINS)

    def load_plugins(self, plugins: typing.List[str]):
        def _import_module_from_filename(plugin: str):
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
                self.plugin_manager.register(mod, plugin)
            except ValueError:
                # Pluin already registered
                pass

    def get_available_stages(self):
        if not self.exclude_default_stages:
            self.load_plugins(DEFAULT_STAGES_PLUGINS)

        stages = itertools.chain.from_iterable(self.plugin_manager.hook.nebari_stage())

        G = nx.DiGraph()

        for stage in stages:
            G.add_node(stage, priority=stage.priority)

        for stage in stages:
            for dep in stage.dependencies:
                output_stages = [s for s in stages if s.output_schema is dep]
                for output_stage in output_stages:
                    G.add_edge(output_stage, stage)

        # stages with no dependencies should be deployed first
        no_dependencies = [node for node, deg in G.in_degree() if deg == 0]
        with_dependencies = [
            node
            for node in nx.algorithms.dag.topological_sort(G)
            if node not in no_dependencies
        ]

        # if stages have the same dependencies, sort based on priority
        sorted_stages = sorted(
            no_dependencies, key=lambda stage: stage.priority
        ) + sorted(with_dependencies, key=lambda stage: stage.priority)

        return sorted_stages

    @property
    def ordered_stages(self):
        return self.get_available_stages()

    @property
    def config_schema(self):
        classes = [schema.Main] + [
            _.input_schema for _ in self.ordered_stages if _.input_schema is not None
        ]
        return type("ConfigSchema", tuple(classes), {})

    def write_configuration(
        self,
        config_filename: Path,
        config: typing.Union[schema.Main, typing.Dict],
        mode: str = "w",
    ):
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False

        with config_filename.open(mode) as f:
            if isinstance(config, self.config_schema):
                yaml.dump(config.dict(), f)
            else:
                yaml.dump(config, f)

        self.config_path = config_filename
        self.read_configuration(self.config_path)

    def read_configuration(
        self,
        config_filename: Path,
        read_environment: bool = True,
    ):
        """Read configuration from multiple sources and apply validation"""
        filename = Path(config_filename)

        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False

        if not filename.is_file():
            raise ValueError(
                f"passed in configuration filename={config_filename} does not exist"
            )

        with filename.open() as f:
            config = self.config_schema(**yaml.load(f.read()))

        if read_environment:
            config = schema.set_config_from_environment_variables(config)

        self.config = config

        return config

    def validate_stages(self):
        pass

    def render_stages(self, template_directory: Path, dry_run: bool = False):
        output_directory = Path(template_directory).resolve()
        if output_directory == Path.home():
            print("ERROR: Deploying Nebari in home directory is not advised!")
            sys.exit(1)

        # mkdir all the way down to repo dir so we can copy .gitignore
        # into it in remove_existing_renders
        output_directory.mkdir(exist_ok=True, parents=True)

        contents = {}
        for stage in self.ordered_stages:
            contents.update(
                stage(output_directory=output_directory, config=self.config).render()
            )

        new, untracked, updated, deleted = inspect_files(
            output_base_dir=str(output_directory),
            ignore_filenames=self._ignore_filenames,
            ignore_directories=self._ignore_directories,
            deleted_paths=self._deleted_paths,
            contents=contents,
        )

        print_rendered_files(new, untracked, updated, deleted)

        if dry_run:
            print("dry-run enabled no files will be created, updated, or deleted")
        else:
            for filename in new | updated:
                output_filename = os.path.join(str(output_directory), filename)
                os.makedirs(os.path.dirname(output_filename), exist_ok=True)

                if isinstance(contents[filename], str):
                    with open(output_filename, "w") as f:
                        f.write(contents[filename])
                else:
                    with open(output_filename, "wb") as f:
                        f.write(contents[filename])

            for path in deleted:
                abs_path = os.path.abspath(os.path.join(str(output_directory), path))

                # be extra cautious that deleted path is within output_directory
                if not abs_path.startswith(str(output_directory)):
                    raise Exception(
                        f"[ERROR] SHOULD NOT HAPPEN filename was about to be deleted but path={abs_path} is outside of output_directory"
                    )

                if os.path.isfile(abs_path):
                    os.remove(abs_path)
                elif os.path.isdir(abs_path):
                    shutil.rmtree(abs_path)

    def deploy_stages(self):
        pass

    def destroy_stages(self):
        pass


nebari_plugin_manager = NebariPluginManager()
