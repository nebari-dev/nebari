from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Optional

from pluggy import HookimplMarker, HookspecMarker
from pydantic import BaseModel
from typer import Typer

from nebari import schema

hookspec = HookspecMarker("nebari")
hookimpl = HookimplMarker("nebari")


class NebariStage(ABC):
    name: ClassVar[str]
    priority: ClassVar[int]
    input_schema: ClassVar[Optional[BaseModel]] = None
    output_schema: ClassVar[BaseModel]

    def __init__(self, output_directory: Path, config: schema.Main):
        self.output_directory = output_directory
        self.config = config

    @abstractmethod
    def render(self):
        ...


@hookspec
def nebari_stage():
    """Registers stages in nebari"""


@hookspec
def nebari_subcommand(cli: Typer):
    """Register Typer subcommand in nebari"""
