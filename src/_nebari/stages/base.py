import contextlib
import inspect
import os
import pathlib
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Tuple

from jinja2 import Environment, FileSystemLoader
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from _nebari.provider import helm, kubernetes, kustomize, terraform
from _nebari.stages.tf_objects import NebariTerraformState
from nebari.hookspecs import NebariStage

KUSTOMIZATION_TEMPLATE = "kustomization.yaml.tmpl"


class NebariKustomizeStage(NebariStage):
    @property
    def template_directory(self):
        return pathlib.Path(inspect.getfile(self.__class__)).parent / "template"

    @property
    def stage_prefix(self):
        return pathlib.Path("stages") / self.name

    @property
    def kustomize_vars(self):
        return {}

    failed_to_create = False
    error_message = ""

    def _get_k8s_client(self, stage_outputs: Dict[str, Dict[str, Any]]):
        try:
            config.load_kube_config(
                config_file=stage_outputs["stages/02-infrastructure"][
                    "kubeconfig_filename"
                ]["value"]
            )
            api_instance = client.ApiClient()
        except ApiException:
            print(
                f"ERROR: After stage={self.name} "
                "unable to connect to kubernetes cluster"
            )
            sys.exit(1)
        return api_instance

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

    def check(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):

        if self.failed_to_create:
            print(
                f"ERROR: After stage={self.name} "
                f"failed to create kubernetes resources"
                f"with error: {self.error_message}"
            )
            sys.exit(1)

    def render(self) -> Dict[pathlib.Path, str]:
        env = Environment(loader=FileSystemLoader(self.template_directory))

        contents = {}
        if not (self.template_directory / KUSTOMIZATION_TEMPLATE).exists():
            raise FileNotFoundError(
                f"ERROR: After stage={self.name} "
                f"{KUSTOMIZATION_TEMPLATE} template file not found in template directory"
            )
        kustomize_template = env.get_template(KUSTOMIZATION_TEMPLATE)
        rendered_kustomization = kustomize_template.render(**self.kustomize_vars)
        with open(self.template_directory / "kustomization.yaml", "w") as f:
            f.write(rendered_kustomization)

        with tempfile.TemporaryDirectory() as temp_dir:
            kustomize.run_kustomize_subprocess(
                [
                    "build",
                    "-o",
                    f"{temp_dir}",
                    "--enable-helm",
                    "--helm-command",
                    f"{helm.download_helm_binary()}",
                    f"{self.template_directory}",
                ]
            )

            # copy crds from the template directory to the temp directory
            crds = self.template_directory.glob("charts/*/*/crds/*.yaml")
            for crd in crds:
                with crd.open("rb") as f:
                    contents[
                        pathlib.Path(
                            self.stage_prefix,
                            "crds",
                            crd.name,
                        )
                    ] = f.read()

            for root, _, filenames in os.walk(temp_dir):
                for filename in filenames:
                    root_filename = pathlib.Path(root) / filename
                    with root_filename.open("rb") as f:
                        contents[
                            pathlib.Path(
                                self.stage_prefix,
                                "manifests",
                                pathlib.Path.relative_to(
                                    pathlib.Path(root_filename), temp_dir
                                ),
                            )
                        ] = f.read()
            # cleanup generated kustomization.yaml
            pathlib.Path(self.template_directory, "kustomization.yaml").unlink()

            # clean up downloaded helm charts
            charts_dir = pathlib.Path(self.template_directory, "charts")
            if charts_dir.exists():
                shutil.rmtree(charts_dir)

            return contents

    # implement the deploy method by taking all of the kubernetes manifests
    # from the manifests sub folder and applying them to the kubernetes
    # cluster using the kubernetes python client in order
    @contextlib.contextmanager
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):

        print(f"Deploying kubernetes resources for {self.name}")
        # get the kubernetes client
        kubernetes_client = self._get_k8s_client(stage_outputs)

        # get the path to the manifests folder
        directory = pathlib.Path(self.output_directory, self.stage_prefix)

        # get the list of all the files in the crds folder
        crds = directory.glob("crds/*.yaml")

        # get the list of all the files in the manifests folder
        manifests = directory.glob("manifests/*.yaml")

        # apply each crd to the kubernetes cluster in alphabetical order
        for crd in sorted(crds):
            print(f"CRD: {crd}")
            try:
                kubernetes.create_from_yaml(kubernetes_client, crd, apply=True)
            except ApiException as e:
                self.failed_to_create = True
                self.error_message = str(e)
            print(f"Applied CRD: {crd}")

        # apply each manifest to the kubernetes cluster in alphabetical order
        for manifest in sorted(manifests):
            print(f"manifest: {manifest}")
            try:
                kubernetes.create_from_yaml(
                    kubernetes_client,
                    manifest,
                    namespace=self.config.namespace,
                    apply=True,
                )
            except ApiException as e:
                self.failed_to_create = True
                self.error_message = str(e)
            print(f"Applied manifest: {manifest}")
        yield

    @contextlib.contextmanager
    def destroy(
        self,
        stage_outputs: Dict[str, Dict[str, Any]],
        status: Dict[str, bool],
        ignore_errors: bool = True,
    ):
        # destroy each manifest in the reverse order
        print(f"Destroying kubernetes resources for {self.name}")

        # get the kubernetes client
        kubernetes_client = self._get_k8s_client(stage_outputs)

        # get the path to the manifests folder
        directory = pathlib.Path(self.output_directory, self.stage_prefix)

        # get the list of all the files in the crds folder
        crds = directory.glob("crds/*.yaml")

        # get the list of all the files in the manifests folder
        manifests = directory.glob("manifests/*.yaml")

        # destroy each manifest in the reverse order

        for manifest in sorted(manifests, reverse=True):

            print(f"Destroyed manifest: {manifest}")
            try:
                kubernetes.delete_from_yaml(kubernetes_client, manifest)
            except ApiException as e:
                self.error_message = str(e)
                if not ignore_errors:
                    raise e

        # destroy each crd in the reverse order

        for crd in sorted(crds, reverse=True):

            print(f"Destroyed CRD: {crd}")
            try:
                kubernetes.delete_from_yaml(kubernetes_client, crd)
            except ApiException as e:
                self.error_message = str(e)
                if not ignore_errors:
                    raise e
        yield


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
