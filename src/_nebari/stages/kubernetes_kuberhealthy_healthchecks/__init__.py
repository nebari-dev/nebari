import contextlib
from typing import Any, Dict, List, Type

from _nebari.stages.base import NebariKustomizeStage
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl


class InputSchema(schema.Base):
    pass


class OutputSchema(schema.Base):
    pass


class KuberHealthyStage(NebariKustomizeStage):
    name = "11-kubernetes-kuberhealthy-healthchecks"
    priority = 110

    input_schema = InputSchema
    output_schema = OutputSchema

    @contextlib.contextmanager
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        if self.config.kuberhealthy.enabled:
            with super().deploy(stage_outputs, disable_prompt):
                yield
        else:
            with self.destroy(stage_outputs, {}):
                yield


@hookimpl
def nebari_stage() -> List[Type[NebariStage]]:
    return [KuberHealthyStage]
