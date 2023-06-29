import contextlib
import pathlib
from typing import Dict, List

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

    # replacement for `stage_outputs`
    required_targets: pydantic.BaseModel = None

    def __init__(self, output_directory: pathlib.Path, config: schema.Main):
        self.output_directory = output_directory
        self.config = config

    def render(self) -> Dict[str, str]:
        """
        Returns a dictionary where the keys represent the file paths and the values represent the file contents.
        """
        return {}

    @contextlib.contextmanager
    def deploy(self):
        yield

    def check(self) -> bool:
        pass

    @contextlib.contextmanager
    def destroy(self, status: Dict[str, bool]):
        yield


@hookspec
def nebari_stage() -> List[NebariStage]:
    """Registers stages in nebari"""


@hookspec
def nebari_subcommand(cli: typer.Typer):
    """Register Typer subcommand in nebari"""
