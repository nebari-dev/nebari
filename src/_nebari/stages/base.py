import contextlib
import inspect
import itertools
import os
import pathlib
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
                contents[
                    os.path.join(
                        self.stage_prefix,
                        os.path.relpath(
                            os.path.join(root, filename), self.template_directory
                        ),
                    )
                ] = open(
                    os.path.join(root, filename),
                    "rb",
                ).read()
        return contents

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        return {}

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

        stage_outputs["stages/" + self.name] = terraform.deploy(**deploy_config)
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
        stage_outputs["stages/" + self.name] = terraform.deploy(
            directory=str(self.output_directory / self.stage_prefix),
            input_vars=self.input_vars(stage_outputs),
            terraform_init=True,
            terraform_import=True,
            terraform_apply=False,
            terraform_destroy=False,
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


def get_available_stages():
    from nebari.plugins import pm

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

    return filtered_stages
