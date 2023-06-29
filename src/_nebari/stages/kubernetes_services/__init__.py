import time
import enum
import json
import os
import sys
import typing
from typing import Any, Dict, List
from urllib.parse import urlencode

import pydantic
from pydantic import Field

from _nebari import constants
from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from _nebari.version import __version__
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl

# check and retry settings
NUM_ATTEMPTS = 10
TIMEOUT = 10  # seconds


def set_docker_image_tag() -> str:
    """Set docker image tag for `jupyterlab`, `jupyterhub`, and `dask-worker`."""
    return os.environ.get("NEBARI_IMAGE_TAG", constants.DEFAULT_NEBARI_IMAGE_TAG)


def set_nebari_dask_version() -> str:
    """Set version of `nebari-dask` meta package."""
    return os.environ.get("NEBARI_DASK_VERSION", constants.DEFAULT_NEBARI_DASK_VERSION)


@schema.yaml_object(schema.yaml)
class AccessEnum(str, enum.Enum):
    all = "all"
    yaml = "yaml"
    keycloak = "keycloak"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


class Prefect(schema.Base):
    enabled: bool = False
    image: typing.Optional[str]
    overrides: typing.Dict = {}
    token: typing.Optional[str]


class CDSDashboards(schema.Base):
    enabled: bool = True
    cds_hide_user_named_servers: bool = True
    cds_hide_user_dashboard_servers: bool = False


class DefaultImages(schema.Base):
    jupyterhub: str = f"quay.io/nebari/nebari-jupyterhub:{set_docker_image_tag()}"
    jupyterlab: str = f"quay.io/nebari/nebari-jupyterlab:{set_docker_image_tag()}"
    dask_worker: str = f"quay.io/nebari/nebari-dask-worker:{set_docker_image_tag()}"


class Storage(schema.Base):
    conda_store: str = "200Gi"
    shared_filesystem: str = "200Gi"


class JupyterHubTheme(schema.Base):
    hub_title: str = "Nebari"
    hub_subtitle: str = "Your open source data science platform"
    welcome: str = """Welcome! Learn about Nebari's features and configurations in <a href="https://www.nebari.dev/docs">the documentation</a>. If you have any questions or feedback, reach the team on <a href="https://www.nebari.dev/docs/community#getting-support">Nebari's support forums</a>."""
    logo: str = "https://raw.githubusercontent.com/nebari-dev/nebari-design/main/logo-mark/horizontal/Nebari-Logo-Horizontal-Lockup-White-text.svg"
    primary_color: str = "#4f4173"
    secondary_color: str = "#957da6"
    accent_color: str = "#32C574"
    text_color: str = "#111111"
    h1_color: str = "#652e8e"
    h2_color: str = "#652e8e"
    version: str = f"v{__version__}"
    display_version: str = "True"  # limitation of theme everything is a str


class Theme(schema.Base):
    jupyterhub: JupyterHubTheme = JupyterHubTheme()


class KubeSpawner(schema.Base):
    cpu_limit: int
    cpu_guarantee: int
    mem_limit: str
    mem_guarantee: str

    class Config:
        extra = "allow"


class JupyterLabProfile(schema.Base):
    access: AccessEnum = AccessEnum.all
    display_name: str
    description: str
    default: bool = False
    users: typing.Optional[typing.List[str]]
    groups: typing.Optional[typing.List[str]]
    kubespawner_override: typing.Optional[KubeSpawner]

    @pydantic.root_validator
    def only_yaml_can_have_groups_and_users(cls, values):
        if values["access"] != AccessEnum.yaml:
            if (
                values.get("users", None) is not None
                or values.get("groups", None) is not None
            ):
                raise ValueError(
                    "Profile must not contain groups or users fields unless access = yaml"
                )
        return values


class DaskWorkerProfile(schema.Base):
    worker_cores_limit: int
    worker_cores: int
    worker_memory_limit: str
    worker_memory: str
    image: typing.Optional[str]

    class Config:
        extra = "allow"


class Profiles(schema.Base):
    jupyterlab: typing.List[JupyterLabProfile] = [
        JupyterLabProfile(
            display_name="Small Instance",
            description="Stable environment with 2 cpu / 8 GB ram",
            default=True,
            kubespawner_override=KubeSpawner(
                cpu_limit=2,
                cpu_guarantee=1.5,
                mem_limit="8G",
                mem_guarantee="5G",
            ),
        ),
        JupyterLabProfile(
            display_name="Medium Instance",
            description="Stable environment with 4 cpu / 16 GB ram",
            kubespawner_override=KubeSpawner(
                cpu_limit=4,
                cpu_guarantee=3,
                mem_limit="16G",
                mem_guarantee="10G",
            ),
        ),
    ]
    dask_worker: typing.Dict[str, DaskWorkerProfile] = {
        "Small Worker": DaskWorkerProfile(
            worker_cores_limit=2,
            worker_cores=1.5,
            worker_memory_limit="8G",
            worker_memory="5G",
            worker_threads=2,
        ),
        "Medium Worker": DaskWorkerProfile(
            worker_cores_limit=4,
            worker_cores=3,
            worker_memory_limit="16G",
            worker_memory="10G",
            worker_threads=4,
        ),
    }

    @pydantic.validator("jupyterlab")
    def check_default(cls, v, values):
        """Check if only one default value is present."""
        default = [attrs["default"] for attrs in v if "default" in attrs]
        if default.count(True) > 1:
            raise TypeError(
                "Multiple default Jupyterlab profiles may cause unexpected problems."
            )
        return v


class CondaEnvironment(schema.Base):
    name: str
    channels: typing.Optional[typing.List[str]]
    dependencies: typing.List[typing.Union[str, typing.Dict[str, typing.List[str]]]]


class CondaStore(schema.Base):
    extra_settings: typing.Dict[str, typing.Any] = {}
    extra_config: str = ""
    image: str = "quansight/conda-store-server"
    image_tag: str = constants.DEFAULT_CONDA_STORE_IMAGE_TAG
    default_namespace: str = "nebari-git"
    object_storage: str = "200Gi"


class NebariWorkflowController(schema.Base):
    enabled: bool = True
    image_tag: str = constants.DEFAULT_NEBARI_WORKFLOW_CONTROLLER_IMAGE_TAG


class ArgoWorkflows(schema.Base):
    enabled: bool = True
    overrides: typing.Dict = {}
    nebari_workflow_controller: NebariWorkflowController = NebariWorkflowController()


class KBatch(schema.Base):
    enabled: bool = True


class Monitoring(schema.Base):
    enabled: bool = True


class ClearML(schema.Base):
    enabled: bool = False
    enable_forward_auth: bool = False
    overrides: typing.Dict = {}


class JupyterHub(schema.Base):
    overrides: typing.Dict = {}


class IdleCuller(schema.Base):
    terminal_cull_inactive_timeout: int = 15
    terminal_cull_interval: int = 5
    kernel_cull_idle_timeout: int = 15
    kernel_cull_interval: int = 5
    kernel_cull_connected: bool = True
    kernel_cull_busy: bool = False
    server_shutdown_no_activity_timeout: int = 15


class JupyterLab(schema.Base):
    idle_culler: IdleCuller = IdleCuller()


class InputSchema(schema.Base):
    prefect: Prefect = Prefect()
    cdsdashboards: CDSDashboards = CDSDashboards()
    default_images: DefaultImages = DefaultImages()
    storage: Storage = Storage()
    theme: Theme = Theme()
    profiles: Profiles = Profiles()
    environments: typing.Dict[str, CondaEnvironment] = {
        "environment-dask.yaml": CondaEnvironment(
            name="dask",
            channels=["conda-forge"],
            dependencies=[
                "python=3.10.8",
                "ipykernel=6.21.0",
                "ipywidgets==7.7.1",
                f"nebari-dask =={set_nebari_dask_version()}",
                "python-graphviz=0.20.1",
                "pyarrow=10.0.1",
                "s3fs=2023.1.0",
                "gcsfs=2023.1.0",
                "numpy=1.23.5",
                "numba=0.56.4",
                "pandas=1.5.3",
                {
                    "pip": [
                        "kbatch==0.4.1",
                    ],
                },
            ],
        ),
        "environment-dashboard.yaml": CondaEnvironment(
            name="dashboard",
            channels=["conda-forge"],
            dependencies=[
                "python=3.10",
                "cdsdashboards-singleuser=0.6.3",
                "cufflinks-py=0.17.3",
                "dash=2.8.1",
                "geopandas=0.12.2",
                "geopy=2.3.0",
                "geoviews=1.9.6",
                "gunicorn=20.1.0",
                "holoviews=1.15.4",
                "ipykernel=6.21.2",
                "ipywidgets=8.0.4",
                "jupyter=1.0.0",
                "jupyterlab=3.6.1",
                "jupyter_bokeh=3.0.5",
                "matplotlib=3.7.0",
                f"nebari-dask=={set_nebari_dask_version()}",
                "nodejs=18.12.1",
                "numpy",
                "openpyxl=3.1.1",
                "pandas=1.5.3",
                "panel=0.14.3",
                "param=1.12.3",
                "plotly=5.13.0",
                "python-graphviz=0.20.1",
                "rich=13.3.1",
                "streamlit=1.9.0",
                "sympy=1.11.1",
                "voila=0.4.0",
                "pip=23.0",
                {
                    "pip": [
                        "streamlit-image-comparison==0.0.3",
                        "noaa-coops==0.2.1",
                        "dash_core_components==2.0.0",
                        "dash_html_components==2.0.0",
                    ],
                },
            ],
        ),
    }
    conda_store: CondaStore = CondaStore()
    argo_workflows: ArgoWorkflows = ArgoWorkflows()
    kbatch: KBatch = KBatch()
    monitoring: Monitoring = Monitoring()
    clearml: ClearML = ClearML()
    jupyterhub: JupyterHub = JupyterHub()
    jupyterlab: JupyterLab = JupyterLab()


class OutputSchema(schema.Base):
    pass


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
    conda_store_environments: Dict[str, CondaEnvironment] = Field(
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
    jupyterhub_profiles: List[JupyterLabProfile] = Field(alias="jupyterlab-profiles")
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


class KubernetesServicesStage(NebariTerraformStage):
    name = "07-kubernetes-services"
    priority = 70

    input_schema = InputSchema
    output_schema = OutputSchema

    def tf_objects(self) -> List[Dict]:
        return [
            NebariTerraformState(self.name, self.config),
            NebariKubernetesProvider(self.config),
            NebariHelmProvider(self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        domain = stage_outputs["stages/04-kubernetes-ingress"]["domain"]
        final_logout_uri = f"https://{domain}/hub/login"

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
                    f"https://{domain}/{ext.urlslug}{ext.logout}",
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
            endpoint=domain,
            realm_id=realm_id,
            node_groups=stage_outputs["stages/02-infrastructure"]["node_selectors"],
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
