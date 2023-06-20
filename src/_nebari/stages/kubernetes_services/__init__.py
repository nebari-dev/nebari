import json
import sys
from typing import Any, Dict, List
from urllib.parse import urlencode

from pydantic import Field

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


# variables shared by multiple services
class KubernetesServicesInputVars(schema.Base):
    name: str
    environment: str
    endpoint: str
    realm_id: str
    node_groups: Dict[str, Dict[str, str]]
    jupyterhub_logout_redirect_url: str = Field(alias="jupyterhub-logout-redirect-url")


def _split_docker_image_name(image_name):
    name, tag = image_name.split(":")
    return {"name": name, "tag": tag}


class ImageNameTag(schema.Base):
    name: str
    tag: str


class CondaStoreInputVars(schema.Base):
    conda_store_environments: Dict[str, schema.CondaEnvironment] = Field(
        alias="conda-store-environments"
    )
    conda_store_default_namespace: str = Field(alias="conda-store-default-namespace")
    conda_store_filesystem_storage: str = Field(alias="conda-store-filesystem-storage")
    conda_store_object_storage: str = Field(alias="conda-store-object-storage")
    conda_store_extra_settings: Dict[str, Any] = Field(
        alias="conda-store-extra-settings"
    )
    conda_store_extra_config: str = Field(alias="conda-store-extra-config")
    conda_store_image: str = Field(alias="conda-store-image")
    conda_store_image_tag: str = Field(alias="conda-store-image-tag")
    conda_store_service_token_scopes: Dict[str, Dict[str, Any]] = Field(
        alias="conda-store-service-token-scopes"
    )


class JupyterhubInputVars(schema.Base):
    cdsdashboards: Dict[str, Any]
    jupyterhub_theme: Dict[str, Any] = Field(alias="jupyterhub-theme")
    jupyterlab_image: ImageNameTag = Field(alias="jupyterlab-image")
    jupyterhub_overrides: List[str] = Field(alias="jupyterhub-overrides")
    jupyterhub_stared_storage: str = Field(alias="jupyterhub-shared-storage")
    jupyterhub_shared_endpoint: str = Field(None, alias="jupyterhub-shared-endpoint")
    jupyterhub_profiles: List[schema.JupyterLabProfile] = Field(
        alias="jupyterlab-profiles"
    )
    jupyterhub_image: ImageNameTag = Field(alias="jupyterhub-image")
    jupyterhub_hub_extraEnv: str = Field(alias="jupyterhub-hub-extraEnv")
    idle_culler_settings: Dict[str, Any] = Field(alias="idle-culler-settings")


class DaskGatewayInputVars(schema.Base):
    dask_worker_image: ImageNameTag = Field(alias="dask-worker-image")
    dask_gateway_profiles: Dict[str, Any] = Field(alias="dask-gateway-profiles")


class MonitoringInputVars(schema.Base):
    monitoring_enabled: bool = Field(alias="monitoring-enabled")


class ArgoWorkflowsInputVars(schema.Base):
    argo_workflows_enabled: bool = Field(alias="argo-workflows-enabled")
    argo_workflows_overrides: List[str] = Field(alias="argo-workflows-overrides")
    nebari_workflow_controller: bool = Field(alias="nebari-workflow-controller")
    workflow_controller_image_tag: str = Field(alias="workflow-controller-image-tag")
    keycloak_read_only_user_credentials: Dict[str, Any] = Field(
        alias="keycloak-read-only-user-credentials"
    )


class KBatchInputVars(schema.Base):
    kbatch_enabled: bool = Field(alias="kbatch-enabled")


class PrefectInputVars(schema.Base):
    prefect_enabled: bool = Field(alias="prefect-enabled")
    prefect_token: str = Field(None, alias="prefect-token")
    prefect_image: str = Field(None, alias="prefect-image")
    prefect_overrides: Dict = Field(alias="prefect-overrides")


class ClearMLInputVars(schema.Base):
    clearml_enabled: bool = Field(alias="clearml-enabled")
    clearml_enable_forwardauth: bool = Field(alias="clearml-enable-forwardauth")
    clearml_overrides: List[str] = Field(alias="clearml-overrides")


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

        realm_id = stage_outputs["stages/06-kubernetes-keycloak-configuration"][
            "realm_id"
        ]["value"]
        jupyterhub_shared_endpoint = (
            stage_outputs["stages/02-infrastructure"]
            .get("nfs_endpoint", {})
            .get("value")
        )
        keycloak_read_only_user_credentials = stage_outputs[
            "stages/06-kubernetes-keycloak-configuration"
        ]["keycloak-read-only-user-credentials"]["value"]

        conda_store_token_scopes = {
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
        }

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

        kubernetes_services_vars = KubernetesServicesInputVars(
            name=self.config.project_name,
            environment=self.config.namespace,
            endpoint=self.config.domain,
            realm_id=realm_id,
            node_groups=_calculate_node_groups(self.config),
            jupyterhub_logout_redirect_url=final_logout_uri,
        )

        conda_store_vars = CondaStoreInputVars(
            conda_store_environments={
                k: v.dict() for k, v in self.config.environments.items()
            },
            conda_store_default_namespace=self.config.conda_store.default_namespace,
            conda_store_filesystem_storage=self.config.storage.conda_store,
            conda_store_object_storage=self.config.conda_store.object_storage,
            conda_store_service_token_scopes=conda_store_token_scopes,
            conda_store_extra_settings=self.config.conda_store.extra_settings,
            conda_store_extra_config=self.config.conda_store.extra_config,
            conda_store_image=self.config.conda_store.image,
            conda_store_image_tag=self.config.conda_store.image_tag,
        )

        jupyterhub_vars = JupyterhubInputVars(
            cdsdashboards=self.config.cdsdashboards.dict(),
            jupyterhub_theme=jupyterhub_theme.dict(),
            jupyterlab_image=_split_docker_image_name(
                self.config.default_images.jupyterlab
            ),
            jupyterhub_stared_storage=self.config.storage.shared_filesystem,
            jupyterhub_shared_endpoint=jupyterhub_shared_endpoint,
            jupyterhub_profiles=self.config.profiles.dict()["jupyterlab"],
            jupyterhub_image=_split_docker_image_name(
                self.config.default_images.jupyterhub
            ),
            jupyterhub_overrides=[json.dumps(self.config.jupyterhub.overrides)],
            jupyterhub_hub_extraEnv=json.dumps(
                self.config.jupyterhub.overrides.get("hub", {}).get("extraEnv", [])
            ),
            idle_culler_settings=self.config.jupyterlab.idle_culler.dict(),
        )

        dask_gateway_vars = DaskGatewayInputVars(
            dask_worker_image=_split_docker_image_name(
                self.config.default_images.dask_worker
            ),
            dask_gateway_profiles=self.config.profiles.dict()["dask_worker"],
        )

        monitoring_vars = MonitoringInputVars(
            monitoring_enabled=self.config.monitoring.enabled,
        )

        argo_workflows_vars = ArgoWorkflowsInputVars(
            argo_workflows_enabled=self.config.argo_workflows.enabled,
            argo_workflows_overrides=[json.dumps(self.config.argo_workflows.overrides)],
            nebari_workflow_controller=self.config.argo_workflows.nebari_workflow_controller.enabled,
            workflow_controller_image_tag=self.config.argo_workflows.nebari_workflow_controller.image_tag,
            keycloak_read_only_user_credentials=keycloak_read_only_user_credentials,
        )

        kbatch_vars = KBatchInputVars(
            kbatch_enabled=self.config.kbatch.enabled,
        )

        prefect_vars = PrefectInputVars(
            prefect_enabled=self.config.prefect.enabled,
            prefect_token=self.config.prefect.token,
            prefect_image=self.config.prefect.image,
            prefect_overrides=self.config.prefect.overrides,
        )

        clearml_vars = ClearMLInputVars(
            clearml_enabled=self.config.clearml.enabled,
            clearml_enable_forwardauth=self.config.clearml.enable_forward_auth,
            clearml_overrides=[json.dumps(self.config.clearml.overrides)],
        )

        return {
            **kubernetes_services_vars.dict(by_alias=True),
            **conda_store_vars.dict(by_alias=True),
            **jupyterhub_vars.dict(by_alias=True),
            **dask_gateway_vars.dict(by_alias=True),
            **monitoring_vars.dict(by_alias=True),
            **argo_workflows_vars.dict(by_alias=True),
            **kbatch_vars.dict(by_alias=True),
            **prefect_vars.dict(by_alias=True),
            **clearml_vars.dict(by_alias=True),
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
