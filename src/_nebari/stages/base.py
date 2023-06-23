import contextlib
import inspect
import itertools
import os
import pathlib
import re
from typing import Any, Dict, List, Tuple

from _nebari.provider import terraform
from _nebari.stages.tf_objects import NebariTerraformState
from nebari.hookspecs import NebariStage


class NebariTerraformStage(NebariStage):
    @property
    def template_directory(self):
        return pathlib.Path(inspect.getfile(self.__class__)).parent / "template"

    @property
    def stage_prefix(self):
        return pathlib.Path("stages") / self.name

    def state_imports(self) -> List[Tuple[str, str]]:
        return []

    def tf_objects(self) -> List[Dict]:
        return [NebariTerraformState(self.name, self.config)]

    def render(self) -> Dict[str, str]:
        contents = {
            str(self.stage_prefix / "_nebari.tf.json"): terraform.tf_render_objects(
                self.tf_objects()
            )
        }
        for root, dirs, filenames in os.walk(self.template_directory):
            for filename in filenames:
                with open(os.path.join(root, filename), "rb") as f:
                    contents[
                        os.path.join(
                            self.stage_prefix,
                            os.path.relpath(
                                os.path.join(root, filename), self.template_directory
                            ),
                        )
                    ] = f.read()
        return contents

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        return {}

    def set_outputs(
        self, stage_outputs: Dict[str, Dict[str, Any]], outputs: Dict[str, Any]
    ):
        stage_key = "stages/" + self.name
        if stage_key not in stage_outputs:
            stage_outputs[stage_key] = {**outputs}
        else:
            stage_outputs[stage_key].update(outputs)

    @contextlib.contextmanager
    def deploy(self, stage_outputs: Dict[str, Dict[str, Any]]):
        deploy_config = dict(
            directory=str(self.output_directory / self.stage_prefix),
            input_vars=self.input_vars(stage_outputs),
        )
        state_imports = self.state_imports()
        if state_imports:
            deploy_config["terraform_import"] = True
            deploy_config["state_imports"] = state_imports

        self.set_outputs(stage_outputs, terraform.deploy(**deploy_config))
        yield

    def check(self, stage_outputs: Dict[str, Dict[str, Any]]):
        pass

    @contextlib.contextmanager
    def destroy(
        self,
        stage_outputs: Dict[str, Dict[str, Any]],
        status: Dict[str, bool],
        ignore_errors: bool = True,
    ):
        self.set_outputs(
            stage_outputs,
            terraform.deploy(
                directory=str(self.output_directory / self.stage_prefix),
                input_vars=self.input_vars(stage_outputs),
                terraform_init=True,
                terraform_import=True,
                terraform_apply=False,
                terraform_destroy=False,
            ),
        )
        yield
        try:
            terraform.deploy(
                directory=str(self.output_directory / self.stage_prefix),
                input_vars=self.input_vars(stage_outputs),
                terraform_init=True,
                terraform_import=True,
                terraform_apply=False,
                terraform_destroy=True,
            )
            status["stages/" + self.name] = True
        except terraform.TerraformException as e:
            if not ignore_errors:
                raise e
            status["stages/" + self.name] = False


def get_available_stages(
    exclude_default_stages: bool = False, exclude_stages: List[str] = []
):
    from nebari.plugins import load_plugins, pm

    DEFAULT_STAGES = [
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

    if not exclude_default_stages:
        load_plugins(DEFAULT_STAGES)

    stages = itertools.chain.from_iterable(pm.hook.nebari_stage())

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
        for exclude_stage in exclude_stages:
            if re.fullmatch(exclude_stage, stage.name) is not None:
                break
        else:
            included_stages.append(stage)

    return included_stages
