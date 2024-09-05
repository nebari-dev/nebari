import enum
import json
import sys
import time
from typing import Any, Dict, List, Optional, Type, Union
from urllib.parse import urlencode

from pydantic import ConfigDict, Field, field_validator, model_validator
from typing_extensions import Self

from _nebari import constants
from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from _nebari.utils import (
    byte_unit_conversion,
    set_docker_image_tag,
    set_nebari_dask_version,
)
from _nebari.version import __version__
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl

# check and retry settings
NUM_ATTEMPTS = 10
TIMEOUT = 10  # seconds


_forwardauth_middleware_name = "traefik-forward-auth"


@schema.yaml_object(schema.yaml)
class AccessEnum(str, enum.Enum):
    all = "all"
    yaml = "yaml"
    keycloak = "keycloak"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


@schema.yaml_object(schema.yaml)
class SharedFsEnum(str, enum.Enum):
    nfs = "nfs"
    cephfs = "cephfs"
    efs = "efs"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


class DefaultImages(schema.Base):
    jupyterhub: str = f"quay.io/nebari/nebari-jupyterhub:{set_docker_image_tag()}"
    jupyterlab: str = f"quay.io/nebari/nebari-jupyterlab:{set_docker_image_tag()}"
    dask_worker: str = f"quay.io/nebari/nebari-dask-worker:{set_docker_image_tag()}"


class Storage(schema.Base):
    type: SharedFsEnum = Field(
        default=None,
        json_schema_extra={"immutable": True},
    )
    conda_store: str = "200Gi"
    shared_filesystem: str = "200Gi"


class JupyterHubTheme(schema.Base):
    hub_title: str = "Nebari"
    hub_subtitle: str = "Your open source data science platform"
    welcome: str = (
        """Welcome! Learn about Nebari's features and configurations in <a href="https://www.nebari.dev/docs">the documentation</a>. If you have any questions or feedback, reach the team on <a href="https://www.nebari.dev/docs/community#getting-support">Nebari's support forums</a>."""
    )
    logo: str = (
        "https://raw.githubusercontent.com/nebari-dev/nebari-design/main/logo-mark/horizontal/Nebari-Logo-Horizontal-Lockup-White-text.svg"
    )
    favicon: str = (
        "https://raw.githubusercontent.com/nebari-dev/nebari-design/main/symbol/favicon.ico"
    )
    primary_color: str = "#4f4173"
    primary_color_dark: str = "#4f4173"
    secondary_color: str = "#957da6"
    secondary_color_dark: str = "#957da6"
    accent_color: str = "#32C574"
    accent_color_dark: str = "#32C574"
    text_color: str = "#111111"
    h1_color: str = "#652e8e"
    h2_color: str = "#652e8e"
    version: str = f"v{__version__}"
    navbar_color: str = "#1c1d26"
    navbar_text_color: str = "#f1f1f6"
    navbar_hover_color: str = "#db96f3"
    display_version: str = "True"  # limitation of theme everything is a str


class Theme(schema.Base):
    jupyterhub: JupyterHubTheme = JupyterHubTheme()


class KubeSpawner(schema.Base):
    cpu_limit: float
    cpu_guarantee: float
    mem_limit: str
    mem_guarantee: str
    model_config = ConfigDict(extra="allow")


class JupyterLabProfile(schema.Base):
    access: AccessEnum = AccessEnum.all
    display_name: str
    description: str
    default: bool = False
    users: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    kubespawner_override: Optional[KubeSpawner] = None

    @model_validator(mode="after")
    def only_yaml_can_have_groups_and_users(self):
        if self.access != AccessEnum.yaml:
            if self.users is not None or self.groups is not None:
                raise ValueError(
                    "Profile must not contain groups or users fields unless access = yaml"
                )
        return self


class DaskWorkerProfile(schema.Base):
    worker_cores_limit: float
    worker_cores: float
    worker_memory_limit: str
    worker_memory: str
    worker_threads: int = 1
    model_config = ConfigDict(extra="allow")


class Profiles(schema.Base):
    jupyterlab: List[JupyterLabProfile] = [
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
    dask_worker: Dict[str, DaskWorkerProfile] = {
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

    @field_validator("jupyterlab")
    @classmethod
    def check_default(cls, value):
        """Check if only one default value is present."""
        default = [attrs["default"] for attrs in value if "default" in attrs]
        if default.count(True) > 1:
            raise TypeError(
                "Multiple default Jupyterlab profiles may cause unexpected problems."
            )
        return value


class CondaEnvironment(schema.Base):
    name: str
    channels: Optional[List[str]] = None
    dependencies: List[Union[str, Dict[str, List[str]]]]


class CondaStore(schema.Base):
    extra_settings: Dict[str, Any] = {}
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
    overrides: Dict = {}
    nebari_workflow_controller: NebariWorkflowController = NebariWorkflowController()


class JHubApps(schema.Base):
    enabled: bool = False


class MonitoringOverrides(schema.Base):
    loki: Dict = {}
    promtail: Dict = {}
    minio: Dict = {}


class Healthchecks(schema.Base):
    enabled: bool = False
    kuberhealthy_helm_version: str = constants.KUBERHEALTHY_HELM_VERSION


class Monitoring(schema.Base):
    enabled: bool = True
    overrides: MonitoringOverrides = MonitoringOverrides()
    minio_enabled: bool = True
    healthchecks: Healthchecks = Healthchecks()


class JupyterLabPioneer(schema.Base):
    enabled: bool = False
    log_format: Optional[str] = None


class Telemetry(schema.Base):
    jupyterlab_pioneer: JupyterLabPioneer = JupyterLabPioneer()


class JupyterHub(schema.Base):
    overrides: Dict = {}


class IdleCuller(schema.Base):
    terminal_cull_inactive_timeout: int = 15
    terminal_cull_interval: int = 5
    kernel_cull_idle_timeout: int = 15
    kernel_cull_interval: int = 5
    kernel_cull_connected: bool = True
    kernel_cull_busy: bool = False
    server_shutdown_no_activity_timeout: int = 15


class JupyterLabGalleryExhibit(schema.Base):
    git: str
    title: str
    homepage: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    account: Optional[str] = None
    token: Optional[str] = None
    branch: Optional[str] = None
    depth: Optional[int] = None


class JupyterLabGallerySettings(schema.Base):
    title: str = "Examples"
    destination: str = "examples"
    exhibits: List[JupyterLabGalleryExhibit] = []
    hide_gallery_without_exhibits: bool = True


class JupyterLab(schema.Base):
    default_settings: Dict[str, Any] = {}
    gallery_settings: JupyterLabGallerySettings = JupyterLabGallerySettings()
    idle_culler: IdleCuller = IdleCuller()
    initial_repositories: List[Dict[str, str]] = []
    preferred_dir: Optional[str] = None


class RookCeph(schema.Base):
    storage_class_name: None | str = None


class InputSchema(schema.Base):
    default_images: DefaultImages = DefaultImages()
    storage: Storage = Storage()
    theme: Theme = Theme()
    profiles: Profiles = Profiles()
    environments: Dict[str, CondaEnvironment] = {
        "environment-dask.yaml": CondaEnvironment(
            name="dask",
            channels=["conda-forge"],
            dependencies=[
                "python==3.11.6",
                "ipykernel==6.26.0",
                "ipywidgets==8.1.1",
                f"nebari-dask=={set_nebari_dask_version()}",
                "python-graphviz==0.20.1",
                "pyarrow==14.0.1",
                "s3fs==2023.10.0",
                "gcsfs==2023.10.0",
                "numpy=1.26.0",
                "numba=0.58.1",
                "pandas=2.1.3",
                "xarray==2023.10.1",
            ],
        ),
        "environment-dashboard.yaml": CondaEnvironment(
            name="dashboard",
            channels=["conda-forge"],
            dependencies=[
                "python==3.11.6",
                "cufflinks-py==0.17.3",
                "dash==2.14.1",
                "geopandas==0.14.1",
                "geopy==2.4.0",
                "geoviews==1.11.0",
                "gunicorn==21.2.0",
                "holoviews==1.18.1",
                "ipykernel==6.26.0",
                "ipywidgets==8.1.1",
                "jupyter==1.0.0",
                "jupyter_bokeh==3.0.7",
                "matplotlib==3.8.1",
                f"nebari-dask=={set_nebari_dask_version()}",
                "nodejs=20.8.1",
                "numpy==1.26.0",
                "openpyxl==3.1.2",
                "pandas==2.1.3",
                "panel==1.3.1",
                "param==2.0.1",
                "plotly==5.18.0",
                "python-graphviz==0.20.1",
                "rich==13.6.0",
                "streamlit==1.28.1",
                "sympy==1.12",
                "voila==0.5.5",
                "xarray==2023.10.1",
                "pip==23.3.1",
                {
                    "pip": [
                        "streamlit-image-comparison==0.0.4",
                        "noaa-coops==0.1.9",
                        "dash_core_components==2.0.0",
                        "dash_html_components==2.0.0",
                    ],
                },
            ],
        ),
    }
    conda_store: CondaStore = CondaStore()
    argo_workflows: ArgoWorkflows = ArgoWorkflows()
    monitoring: Monitoring = Monitoring()
    telemetry: Telemetry = Telemetry()
    jupyterhub: JupyterHub = JupyterHub()
    jupyterlab: JupyterLab = JupyterLab()
    jhub_apps: JHubApps = JHubApps()
    ceph: RookCeph = RookCeph()

    def _set_storage_type_default_value(self):
        if self.storage.type is None:
            if self.provider == schema.ProviderEnum.aws:
                self.storage.type = SharedFsEnum.efs
            else:
                self.storage.type = SharedFsEnum.nfs

    @model_validator(mode="after")
    def custom_validation(self) -> Self:
        self._set_storage_type_default_value()

        if (
            self.storage.type == SharedFsEnum.cephfs
            and self.provider == schema.ProviderEnum.local
        ):
            raise ValueError(
                f'storage.type: "{self.storage.type.value}" is not supported for provider: "{self.provider.value}"'
            )

        if (
            self.storage.type == SharedFsEnum.efs
            and self.provider != schema.ProviderEnum.aws
        ):
            raise ValueError(
                f'storage.type: "{self.storage.type.value}" is only supported for provider: "{schema.ProviderEnum.aws.value}"'
            )
        return self


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
    forwardauth_middleware_name: str = _forwardauth_middleware_name
    cert_secret_name: Optional[str] = None


def _split_docker_image_name(image_name):
    name, tag = image_name.split(":")
    return {"name": name, "tag": tag}


class ImageNameTag(schema.Base):
    name: str
    tag: str


class RookCephInputVars(schema.Base):
    rook_ceph_storage_class_name: None | str = None


class CondaStoreInputVars(schema.Base):
    conda_store_environments: Dict[str, CondaEnvironment] = Field(
        alias="conda-store-environments"
    )
    conda_store_default_namespace: str = Field(alias="conda-store-default-namespace")
    conda_store_filesystem_storage: float = Field(
        alias="conda-store-filesystem-storage"
    )
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

    @field_validator("conda_store_filesystem_storage", mode="before")
    @classmethod
    def handle_units(cls, value: Optional[str]) -> float:
        return byte_unit_conversion(value, "GiB")


class JupyterhubInputVars(schema.Base):
    jupyterhub_theme: Dict[str, Any] = Field(alias="jupyterhub-theme")
    jupyterlab_image: ImageNameTag = Field(alias="jupyterlab-image")
    jupyterlab_default_settings: Dict[str, Any] = Field(
        alias="jupyterlab-default-settings"
    )
    jupyterlab_gallery_settings: JupyterLabGallerySettings = Field(
        alias="jupyterlab-gallery-settings"
    )
    initial_repositories: str = Field(alias="initial-repositories")
    jupyterhub_overrides: List[str] = Field(alias="jupyterhub-overrides")
    jupyterhub_shared_storage: float = Field(alias="jupyterhub-shared-storage")
    jupyterhub_shared_endpoint: Optional[str] = Field(
        alias="jupyterhub-shared-endpoint", default=None
    )
    jupyterhub_profiles: List[JupyterLabProfile] = Field(alias="jupyterlab-profiles")
    jupyterhub_image: ImageNameTag = Field(alias="jupyterhub-image")
    jupyterhub_hub_extraEnv: str = Field(alias="jupyterhub-hub-extraEnv")
    idle_culler_settings: Dict[str, Any] = Field(alias="idle-culler-settings")
    argo_workflows_enabled: bool = Field(alias="argo-workflows-enabled")
    jhub_apps_enabled: bool = Field(alias="jhub-apps-enabled")
    cloud_provider: str = Field(alias="cloud-provider")
    jupyterlab_preferred_dir: Optional[str] = Field(alias="jupyterlab-preferred-dir")
    shared_fs_type: SharedFsEnum

    @field_validator("jupyterhub_shared_storage", mode="before")
    @classmethod
    def handle_units(cls, value: Optional[str]) -> float:
        return byte_unit_conversion(value, "GiB")


class DaskGatewayInputVars(schema.Base):
    dask_worker_image: ImageNameTag = Field(alias="dask-worker-image")
    dask_gateway_profiles: Dict[str, Any] = Field(alias="dask-gateway-profiles")
    cloud_provider: str = Field(alias="cloud-provider")
    forwardauth_middleware_name: str = _forwardauth_middleware_name


class MonitoringInputVars(schema.Base):
    monitoring_enabled: bool = Field(alias="monitoring-enabled")
    minio_enabled: bool = Field(alias="minio-enabled")
    grafana_loki_overrides: List[str] = Field(alias="grafana-loki-overrides")
    grafana_promtail_overrides: List[str] = Field(alias="grafana-promtail-overrides")
    grafana_loki_minio_overrides: List[str] = Field(
        alias="grafana-loki-minio-overrides"
    )


class TelemetryInputVars(schema.Base):
    jupyterlab_pioneer_enabled: bool = Field(alias="jupyterlab-pioneer-enabled")
    jupyterlab_pioneer_log_format: Optional[str] = Field(
        alias="jupyterlab-pioneer-log-format"
    )


class ArgoWorkflowsInputVars(schema.Base):
    argo_workflows_enabled: bool = Field(alias="argo-workflows-enabled")
    argo_workflows_overrides: List[str] = Field(alias="argo-workflows-overrides")
    nebari_workflow_controller: bool = Field(alias="nebari-workflow-controller")
    workflow_controller_image_tag: str = Field(alias="workflow-controller-image-tag")
    keycloak_read_only_user_credentials: Dict[str, Any] = Field(
        alias="keycloak-read-only-user-credentials"
    )


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
        cloud_provider = self.config.provider.value
        jupyterhub_shared_endpoint = (
            stage_outputs["stages/02-infrastructure"]
            .get("nfs_endpoint", {})
            .get("value")
        )
        keycloak_read_only_user_credentials = stage_outputs[
            "stages/06-kubernetes-keycloak-configuration"
        ]["keycloak-read-only-user-credentials"]["value"]

        conda_store_token_scopes = {
            "dask-gateway": {
                "primary_namespace": "",
                "role_bindings": {
                    "*/*": ["viewer"],
                },
            },
            "argo-workflows-jupyter-scheduler": {
                "primary_namespace": "",
                "role_bindings": {
                    "*/*": ["viewer"],
                },
            },
            "jhub-apps": {
                "primary_namespace": "",
                "role_bindings": {
                    "*/*": ["viewer"],
                },
            },
            "conda-store-service-account": {
                "primary_namespace": "",
                "role_bindings": {
                    "*/*": ["admin"],
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
            cert_secret_name=(
                self.config.certificate.secret_name
                if self.config.certificate.type == "existing"
                else None
            ),
        )

        rook_ceph_vars = RookCephInputVars()

        conda_store_vars = CondaStoreInputVars(
            conda_store_environments={
                k: v.model_dump() for k, v in self.config.environments.items()
            },
            conda_store_default_namespace=self.config.conda_store.default_namespace,
            conda_store_filesystem_storage=self.config.storage.conda_store,
            conda_store_object_storage=self.config.storage.conda_store,
            conda_store_service_token_scopes=conda_store_token_scopes,
            conda_store_extra_settings=self.config.conda_store.extra_settings,
            conda_store_extra_config=self.config.conda_store.extra_config,
            conda_store_image=self.config.conda_store.image,
            conda_store_image_tag=self.config.conda_store.image_tag,
        )

        jupyterhub_vars = JupyterhubInputVars(
            jupyterhub_theme=jupyterhub_theme.model_dump(),
            jupyterlab_image=_split_docker_image_name(
                self.config.default_images.jupyterlab
            ),
            jupyterhub_shared_storage=self.config.storage.shared_filesystem,
            jupyterhub_shared_endpoint=jupyterhub_shared_endpoint,
            cloud_provider=cloud_provider,
            jupyterhub_profiles=self.config.profiles.model_dump()["jupyterlab"],
            jupyterhub_image=_split_docker_image_name(
                self.config.default_images.jupyterhub
            ),
            jupyterhub_overrides=[json.dumps(self.config.jupyterhub.overrides)],
            jupyterhub_hub_extraEnv=json.dumps(
                self.config.jupyterhub.overrides.get("hub", {}).get("extraEnv", [])
            ),
            idle_culler_settings=self.config.jupyterlab.idle_culler.model_dump(),
            argo_workflows_enabled=self.config.argo_workflows.enabled,
            jhub_apps_enabled=self.config.jhub_apps.enabled,
            initial_repositories=str(self.config.jupyterlab.initial_repositories),
            jupyterlab_default_settings=self.config.jupyterlab.default_settings,
            jupyterlab_gallery_settings=self.config.jupyterlab.gallery_settings,
            jupyterlab_preferred_dir=self.config.jupyterlab.preferred_dir,
            shared_fs_type=(
                # efs is equivalent to nfs in these modules
                SharedFsEnum.nfs
                if self.config.storage.type == SharedFsEnum.efs
                else self.config.storage.type
            ),
        )

        dask_gateway_vars = DaskGatewayInputVars(
            dask_worker_image=_split_docker_image_name(
                self.config.default_images.dask_worker
            ),
            dask_gateway_profiles=self.config.profiles.model_dump()["dask_worker"],
            cloud_provider=cloud_provider,
        )

        monitoring_vars = MonitoringInputVars(
            monitoring_enabled=self.config.monitoring.enabled,
            minio_enabled=self.config.monitoring.minio_enabled,
            grafana_loki_overrides=[json.dumps(self.config.monitoring.overrides.loki)],
            grafana_promtail_overrides=[
                json.dumps(self.config.monitoring.overrides.promtail)
            ],
            grafana_loki_minio_overrides=[
                json.dumps(self.config.monitoring.overrides.minio)
            ],
        )

        telemetry_vars = TelemetryInputVars(
            jupyterlab_pioneer_enabled=self.config.telemetry.jupyterlab_pioneer.enabled,
            jupyterlab_pioneer_log_format=self.config.telemetry.jupyterlab_pioneer.log_format,
        )

        argo_workflows_vars = ArgoWorkflowsInputVars(
            argo_workflows_enabled=self.config.argo_workflows.enabled,
            argo_workflows_overrides=[json.dumps(self.config.argo_workflows.overrides)],
            nebari_workflow_controller=self.config.argo_workflows.nebari_workflow_controller.enabled,
            workflow_controller_image_tag=self.config.argo_workflows.nebari_workflow_controller.image_tag,
            keycloak_read_only_user_credentials=keycloak_read_only_user_credentials,
        )

        return {
            **kubernetes_services_vars.model_dump(by_alias=True),
            **rook_ceph_vars.model_dump(by_alias=True),
            **conda_store_vars.model_dump(by_alias=True),
            **jupyterhub_vars.model_dump(by_alias=True),
            **dask_gateway_vars.model_dump(by_alias=True),
            **monitoring_vars.model_dump(by_alias=True),
            **argo_workflows_vars.model_dump(by_alias=True),
            **telemetry_vars.model_dump(by_alias=True),
        }

    def check(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
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
def nebari_stage() -> List[Type[NebariStage]]:
    return [KubernetesServicesStage]
