import contextlib
import os
import pathlib
import sys
from typing import Any, Dict, List, Type

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from _nebari.apply_from_yaml import create_from_yaml
from _nebari.stages.base import NebariTerraformStage
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl


class InputSchema(schema.Base):
    pass


class OutputSchema(schema.Base):
    pass


class KubernetesTestStage(NebariTerraformStage):
    name = "10-kubernetes-kuberhealthy"
    priority = 100

    input_schema = InputSchema
    output_schema = OutputSchema

    failed_to_create = False
    error_message = ""

    def get_k8s_client(self, stage_outputs: Dict[str, Dict[str, Any]]):
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

    def tf_objects(self) -> List[Dict]:
        return []

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        return {}

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

        path = pathlib.Path(__file__).parent

        with open(f"{path}/template/01-kuberhealthy.yaml", "r") as f:
            kuberhealthy_manifest = f.read()

            contents = {
                (
                    self.stage_prefix / "01-kuberhealthy-prometheus-operator.yaml"
                ): kuberhealthy_manifest
            }

            for root, _, filenames in os.walk(self.template_directory):
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

    # implement the deploy method by taking all of the kubernetes manifests
    # from the manifests sub folder and applying them to the kubernetes
    # cluster using the kubernetes python client in order
    @contextlib.contextmanager
    def deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):

        print(f"Deploying kubernetes resources for stage={self.name}")
        # get the kubernetes client
        kubernetes_client = self.get_k8s_client(stage_outputs)

        # get the path to the manifests folder
        directory = pathlib.Path(self.output_directory, self.stage_prefix)

        # get the list of all the files in the manifests folder
        manifests = directory.glob("*.yaml")

        # apply each manifest to the kubernetes cluster
        for manifest in manifests:
            print(f"manifest: {manifest}")
            try:
                create_from_yaml(
                    kubernetes_client, manifest, namespace="kuberhealthy", apply=True
                )
            except ApiException as e:
                self.failed_to_create = True
                self.error_message = str(e)
            print(f"Applied manifest: {manifest}")
        yield


@hookimpl
def nebari_stage() -> List[Type[NebariStage]]:
    return [KubernetesTestStage]
