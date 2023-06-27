import collections
import importlib
import itertools
import os
import re
import sys
import typing
from pathlib import Path

import pluggy
import rich
import typer
from pydantic import BaseModel, create_model
from rich.table import Table
from typer.core import TyperGroup

from _nebari.version import __version__
from nebari import hookspecs, schema

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

    ordered_stages: typing.List[hookspecs.NebariStage] = []
    exclude_default_stages: bool = False
    exclude_stages: typing.List[str] = []

    cli: typer.Typer = None

    schema_name: str = "NebariConfig"
    config_schema: typing.Union[BaseModel, None] = None
    config_path: typing.Union[Path, None] = None
    config: typing.Union[BaseModel, None] = None

    def __init__(self) -> None:
        self.plugin_manager.add_hookspecs(hookspecs)

        if not hasattr(sys, "_called_from_test"):
            # Only load plugins if not running tests
            self.plugin_manager.load_setuptools_entrypoints("nebari")

        self.load_subcommands(DEFAULT_SUBCOMMAND_PLUGINS)
        self.ordered_stages = self.get_available_stages()
        self.config_schema = self.extend_schema()

    def load_subcommands(self, subcommand: typing.List[str]):
        self._load_plugins(subcommand)

    def load_stages(self, stages: typing.List[str]):
        self._load_plugins(stages)

    def _load_plugins(self, plugins: typing.List[str]):
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
            self.load_stages(DEFAULT_STAGES_PLUGINS)

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

    def load_config(self, config_path: typing.Union[str, Path]):
        if isinstance(config_path, str):
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file {config_path} not found")

        self.config_path = config_path
        self.config = schema.read_configuration(config_path)

    def _create_dynamic_schema(
        self, base: BaseModel, stage: BaseModel, stage_name: str
    ) -> BaseModel:
        stage_fields = {
            n: (f.type_, f.default if f.default is not None else ...)
            for n, f in stage.__fields__.items()
        }
        # ensure top-level key for `stage` is set to `stage_name`
        stage_model = create_model(stage_name, __base__=schema.Base, **stage_fields)
        extra_fields = {stage_name: (stage_model, None)}
        return create_model(self.schema_name, __base__=base, **extra_fields)

    def extend_schema(self, base_schema: BaseModel = schema.Main) -> BaseModel:
        config_schema = base_schema
        for stages in self.ordered_stages:
            if stages.stage_schema:
                config_schema = self._create_dynamic_schema(
                    config_schema,
                    stages.stage_schema,
                    stages.name,
                )
        return config_schema

    def _version_callback(self, value: bool):
        if value:
            typer.echo(__version__)
            raise typer.Exit()

    def create_cli(self) -> typer.Typer:
        class OrderCommands(TyperGroup):
            def list_commands(self, ctx: typer.Context):
                """Return list of commands in the order appear."""
                return list(self.commands)

        cli = typer.Typer(
            cls=OrderCommands,
            help="Nebari CLI 🪴",
            add_completion=False,
            no_args_is_help=True,
            rich_markup_mode="rich",
            pretty_exceptions_show_locals=False,
            context_settings={"help_option_names": ["-h", "--help"]},
        )

        @cli.callback()
        def common(
            ctx: typer.Context,
            version: bool = typer.Option(
                None,
                "-V",
                "--version",
                help="Nebari version number",
                callback=self._version_callback,
            ),
            extra_stages: typing.List[str] = typer.Option(
                [],
                "--import-plugin",
                help="Import nebari plugin",
            ),
            extra_subcommands: typing.List[str] = typer.Option(
                [],
                "--import-subcommand",
                help="Import nebari subcommand",
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
            try:
                self.load_stages(extra_stages)
                self.load_subcommands(extra_subcommands)
            except ModuleNotFoundError:
                typer.echo(
                    "ERROR: Python module {e.name} not found. Make sure that the module is in your python path {sys.path}"
                )
                typer.Exit()

            self.exclude_default_stages = exclude_default_stages
            self.exclude_stages = excluded_stages
            self.ordered_stages = self.get_available_stages()
            self.config_schema = self.extend_schema()

        @cli.command()
        def info(ctx: typer.Context):
            """
            Display the version and available hooks for Nebari.
            """
            rich.print(f"Nebari version: {__version__}")

            hooks = collections.defaultdict(list)
            for plugin in self.plugin_manager.get_plugins():
                for hook in self.plugin_manager.get_hookcallers(plugin):
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
            for stage in self.ordered_stages:
                table.add_row(
                    stage.name,
                    str(stage.priority),
                    f"{stage.__module__}.{stage.__name__}",
                )

            rich.print(table)

        self.plugin_manager.hook.nebari_subcommand(cli=cli)

        self.cli = cli
        self.cli()

        return cli


nebari_plugin_manager = NebariPluginManager()
