import contextlib
from typing import Any, Dict, List, Type

from _nebari.stages.base import NebariKustomizeStage
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl


class KuberhealthyInputSchema(schema.Base):
    enabled: bool = True


class InputSchema(schema.Base):
    kuberhealthy: KuberhealthyInputSchema = KuberhealthyInputSchema()


class OutputSchema(schema.Base):
    pass


class KuberHealthyStage(NebariKustomizeStage):
    name = "10-kubernetes-kuberhealthy"
    priority = 100

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
