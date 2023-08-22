import contextlib
import inspect
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

    def render(self) -> Dict[pathlib.Path, str]:
        contents = {
            (self.stage_prefix / "_nebari.tf.json"): terraform.tf_render_objects(
                self.tf_objects()
            )
        }
        for root, dirs, filenames in os.walk(self.template_directory):
            for filename in filenames:
                root_filename = pathlib.Path(root) / filename
                with root_filename.open("rb") as f:
                    contents[
                        pathlib.Path(
                            self.stage_prefix,
                            pathlib.Path.relative_to(
                                pathlib.Path(root_filename), self.template_directory
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
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        deploy_config = dict(
            directory=str(self.output_directory / self.stage_prefix),
            input_vars=self.input_vars(stage_outputs),
        )
        state_imports = self.state_imports()
        if state_imports:
            deploy_config["terraform_import"] = True
            deploy_config["state_imports"] = state_imports

        self.set_outputs(stage_outputs, terraform.deploy(**deploy_config))
        self.post_deploy(stage_outputs, disable_prompt)
        yield

    def post_deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        pass

    def check(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
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
