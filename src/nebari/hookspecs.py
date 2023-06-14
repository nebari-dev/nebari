import contextlib
import pathlib
from collections.abc import Iterable
from typing import Any, Dict

from pluggy import HookimplMarker, HookspecMarker

hookspec = HookspecMarker("nebari")
hookimpl = HookimplMarker("nebari")

from nebari import schema


class NebariStage:
    name = None
    priority = None

    def __init__(self, output_directory: pathlib.Path, config: schema.Main):
        self.output_directory = output_directory
        self.config = config

    def validate(self):
        pass

    def render(self, output_directory: pathlib.Path):
        raise NotImplementedError()

    @contextlib.contextmanager
    def deploy(self, stage_outputs: Dict[str, Dict[str, Any]]):
        raise NotImplementedError()

    def check(self, stage_outputs: Dict[str, Dict[str, Any]]) -> bool:
        pass

    @contextlib.contextmanager
    def destroy(
        self, stage_outputs: Dict[str, Dict[str, Any]], status: Dict[str, bool]
    ):
        raise NotImplementedError()


@hookspec
def nebari_stage(
    install_directory: pathlib.Path, config: schema.Main
) -> Iterable[NebariStage]:
    """Registers stages in nebari"""
