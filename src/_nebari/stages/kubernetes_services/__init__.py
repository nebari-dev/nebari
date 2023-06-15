import json
import sys
from typing import Any, Dict, List
from urllib.parse import urlencode

from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl

# check and retry settings
NUM_ATTEMPTS = 10
TIMEOUT = 10  # seconds


def _split_docker_image_name(image_name):
    name, tag = image_name.split(":")
    return {"name": name, "tag": tag}


def _calculate_node_groups(config: schema.Main):
    if config.provider == schema.ProviderEnum.aws:
        return {
            group: {"key": "eks.amazonaws.com/nodegroup", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.gcp:
        return {
            group: {"key": "cloud.google.com/gke-nodepool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.azure:
        return {
            group: {"key": "azure-node-pool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.do:
        return {
            group: {"key": "doks.digitalocean.com/node-pool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.existing:
        return config.existing.node_selectors
    else:
        return config.local.dict()["node_selectors"]


class KubernetesServicesStage(NebariTerraformStage):
    name = "07-kubernetes-services"
    priority = 70

    def tf_objects(self) -> List[Dict]:
        return [
            NebariTerraformState(self.name, self.config),
            NebariKubernetesProvider(self.config),
            NebariHelmProvider(self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        final_logout_uri = f"https://{self.config.domain}/hub/login"

        # Compound any logout URLs from extensions so they are are logged out in succession
        # when Keycloak and JupyterHub are logged out
        for ext in self.config.tf_extensions:
            if ext.logout != "":
                final_logout_uri = "{}?{}".format(
                    f"https://{self.config.domain}/{ext.urlslug}{ext.logout}",
                    urlencode({"redirect_uri": final_logout_uri}),
                )

        jupyterhub_theme = self.config.theme.jupyterhub
        if self.config.theme.jupyterhub.display_version and (
            not self.config.theme.jupyterhub.version
        ):
            jupyterhub_theme.update({"version": f"v{self.config.nebari_version}"})

        return {
            "name": self.config.project_name,
            "environment": self.config.namespace,
            "endpoint": self.config.domain,
            "realm_id": stage_outputs["stages/06-kubernetes-keycloak-configuration"][
                "realm_id"
            ]["value"],
            "node_groups": _calculate_node_groups(self.config),
            # conda-store
            "conda-store-environments": {
                k: v.dict() for k, v in self.config.environments.items()
            },
            "conda-store-filesystem-storage": self.config.storage.conda_store,
            "conda-store-service-token-scopes": {
                "cdsdashboards": {
                    "primary_namespace": "cdsdashboards",
                    "role_bindings": {
                        "*/*": ["viewer"],
                    },
                },
                "dask-gateway": {
                    "primary_namespace": "",
                    "role_bindings": {
                        "*/*": ["viewer"],
                    },
                },
            },
            "conda-store-default-namespace": self.config.conda_store.default_namespace,
            "conda-store-extra-settings": self.config.conda_store.extra_settings,
            "conda-store-extra-config": self.config.conda_store.extra_config,
            "conda-store-image-tag": self.config.conda_store.image_tag,
            # jupyterhub
            "cdsdashboards": self.config.cdsdashboards.dict(),
            "jupyterhub-theme": self.config.theme.jupyterhub.dict(),
            "jupyterhub-image": _split_docker_image_name(
                self.config.default_images.jupyterhub
            ),
            "jupyterhub-shared-storage": self.config.storage.shared_filesystem,
            "jupyterhub-shared-endpoint": stage_outputs["stages/02-infrastructure"]
            .get("nfs_endpoint", {})
            .get("value"),
            "jupyterlab-profiles": self.config.profiles.dict()["jupyterlab"],
            "jupyterlab-image": _split_docker_image_name(
                self.config.default_images.jupyterlab
            ),
            "jupyterhub-overrides": [json.dumps(self.config.jupyterhub.overrides)],
            "jupyterhub-hub-extraEnv": json.dumps(
                self.config.jupyterhub.overrides.get("hub", {}).get("extraEnv", [])
            ),
            # jupyterlab
            "idle-culler-settings": self.config.jupyterlab.idle_culler.dict(),
            # dask-gateway
            "dask-worker-image": _split_docker_image_name(
                self.config.default_images.dask_worker
            ),
            "dask-gateway-profiles": self.config.profiles.dict()["dask_worker"],
            # monitoring
            "monitoring-enabled": self.config.monitoring.enabled,
            # argo-worfklows
            "argo-workflows-enabled": self.config.argo_workflows.enabled,
            "argo-workflows-overrides": [
                json.dumps(self.config.argo_workflows.overrides)
            ],
            "nebari-workflow-controller": self.config.argo_workflows.nebari_workflow_controller.enabled,
            "keycloak-read-only-user-credentials": stage_outputs[
                "stages/06-kubernetes-keycloak-configuration"
            ]["keycloak-read-only-user-credentials"]["value"],
            "workflow-controller-image-tag": self.config.argo_workflows.nebari_workflow_controller.image_tag,
            # kbatch
            "kbatch-enabled": self.config.kbatch.enabled,
            # prefect
            "prefect-enabled": self.config.prefect.enabled,
            "prefect-token": self.config.prefect.token,
            "prefect-image": self.config.prefect.image,
            "prefect-overrides": self.config.prefect.overrides,
            # clearml
            "clearml-enabled": self.config.clearml.enabled,
            "clearml-enable-forwardauth": self.config.clearml.enable_forward_auth,
            "clearml-overrides": [json.dumps(self.config.clearml.overrides)],
            "jupyterhub-logout-redirect-url": final_logout_uri,
        }

    def check(self, stage_outputs: Dict[str, Dict[str, Any]]):
        directory = "stages/07-kubernetes-services"
        import requests

        # suppress insecure warnings
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        def _attempt_connect_url(
            url, verify=False, num_attempts=NUM_ATTEMPTS, timeout=TIMEOUT
        ):
            for i in range(num_attempts):
                response = requests.get(url, verify=verify, timeout=timeout)
                if response.status_code < 400:
                    print(f"Attempt {i+1} health check succeeded for url={url}")
                    return True
                else:
                    print(f"Attempt {i+1} health check failed for url={url}")
                time.sleep(timeout)
            return False

        services = stage_outputs[directory]["service_urls"]["value"]
        for service_name, service in services.items():
            service_url = service["health_url"]
            if service_url and not _attempt_connect_url(service_url):
                print(
                    f"ERROR: Service {service_name} DOWN when checking url={service_url}"
                )
                sys.exit(1)


@hookimpl
def nebari_stage() -> List[NebariStage]:
    return [KubernetesServicesStage]
