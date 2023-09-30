from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Any, ClassVar, Dict, Optional, Type

from pluggy import HookimplMarker, HookspecMarker
from pydantic import BaseModel
from typer import Typer

from nebari import schema

hookspec = HookspecMarker("nebari")
hookimpl = HookimplMarker("nebari")


class NebariStage(ABC):
    name: ClassVar[str]
    priority: ClassVar[int]
    input_schema: ClassVar[Optional[Type[BaseModel]]] = None
    output_schema: ClassVar[Type[BaseModel]]

    def __init__(self, output_directory: Path, config: schema.Main):
        self.output_directory = output_directory
        self.config = config

    @abstractmethod
    def render(self):
        ...

    @abstractmethod
    def check(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ) -> None:
        ...

    @abstractmethod
    @contextmanager
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        ...

    @abstractmethod
    @contextmanager
    def destroy(
        self,
        stage_outputs: Dict[str, Dict[str, Any]],
        status: Dict[str, bool],
        ignore_errors: bool,
    ):
        ...


@hookspec
def nebari_stage():
    """Registers stages in nebari"""


@hookspec
def nebari_subcommand(cli: Typer):
    """Register Typer subcommand in nebari"""
