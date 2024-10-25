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
    name = "10-kubernetes-kuberhealthy"
    priority = 100

    input_schema = InputSchema
    output_schema = OutputSchema

    @property
    def kustomize_vars(self):
        return {
            "namespace": self.config.namespace,
            "kuberhealthy_helm_version": self.config.monitoring.healthchecks.kuberhealthy_helm_version,
        }

    @contextlib.contextmanager
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        if self.config.monitoring.healthchecks.enabled:
            with super().deploy(stage_outputs, disable_prompt):
                yield
        else:
            with self.destroy(stage_outputs, {}):
                yield


@hookimpl
def nebari_stage() -> List[Type[NebariStage]]:
    return [KuberHealthyStage]
