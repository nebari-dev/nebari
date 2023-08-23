import contextlib
import pathlib
from typing import Any, Dict, List

import pydantic
import typer
from pluggy import HookimplMarker, HookspecMarker

from nebari import schema

hookspec = HookspecMarker("nebari")
hookimpl = HookimplMarker("nebari")


class NebariStage:
    name: str = None
    priority: int = None

    input_schema: pydantic.BaseModel = None
    output_schema: pydantic.BaseModel = None

    def __init__(self, output_directory: pathlib.Path, config: schema.Main):
        self.output_directory = output_directory
        self.config = config

    def render(self) -> Dict[str, str]:
        return {}

    @contextlib.contextmanager
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        yield

    def check(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ) -> bool:
        pass

    @contextlib.contextmanager
    def destroy(
        self, stage_outputs: Dict[str, Dict[str, Any]], status: Dict[str, bool]
    ):
        yield


@hookspec
def nebari_stage() -> List[NebariStage]:
    """Registers stages in nebari"""


@hookspec
def nebari_subcommand(cli: typer.Typer):
    """Register Typer subcommand in nebari"""
