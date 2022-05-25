# remove after next kubespawner release past 1/20/2022
# https://github.com/jupyterhub/kubespawner/pull/558
import kubernetes.client.models
import z2jh
from kubespawner import KubeSpawner

kubernetes.client.models.V1EndpointPort = kubernetes.client.models.CoreV1EndpointPort

cdsdashboards = z2jh.get_config("custom.cdsdashboards")
conda_store_environments = z2jh.get_config("custom.environments")

if cdsdashboards["enabled"]:
    from cdsdashboards.app import CDS_TEMPLATE_PATHS
    from cdsdashboards.builder.kubebuilder import KubeBuilder
    from cdsdashboards.hubextension import cds_extra_handlers
    from cdsdashboards.hubextension.spawners.variablekube import VariableKubeSpawner

    c.JupyterHub.allow_named_servers = True
    c.JupyterHub.extra_handlers.extend(cds_extra_handlers)
    c.JupyterHub.template_paths.extend(CDS_TEMPLATE_PATHS)
    c.JupyterHub.spawner_class = VariableKubeSpawner
    c.CDSDashboardsConfig.builder_class = KubeBuilder
    c.VariableMixin.default_presentation_cmd = [
        "python3",
        "-m",
        "jhsingle_native_proxy.main",
    ]
    c.JupyterHub.default_url = "/hub/home"

    # Force dashboard creator to select an instance size
    c.CDSDashboardsConfig.spawn_default_options = False

    c.CDSDashboardsConfig.conda_envs = [
        environment["name"] for _, environment in conda_store_environments.items()
    ]
else:
    c.JupyterHub.allow_named_servers = False
    c.JupyterHub.spawner_class = KubeSpawner
