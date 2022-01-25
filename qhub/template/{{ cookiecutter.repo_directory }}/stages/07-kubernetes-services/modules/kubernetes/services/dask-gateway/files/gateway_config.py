import os
import json

from aiohttp import web
from dask_gateway_server.options import Options, Select, Mapping
from dask_gateway_server.auth import JupyterHubAuthenticator


def dask_gateway_config(path="/var/lib/dask-gateway/config.json"):
    with open(path) as f:
        return json.load(f)
config = dask_gateway_config()


c.DaskGateway.log_level = config['gateway']['loglevel']

# Configure addresses
c.DaskGateway.address = ":8000"
c.KubeBackend.api_url = f'http://{config["gateway_service_name"]}.{config["gateway_service_namespace"]}:8000/api'

c.DaskGateway.backend_class = "dask_gateway_server.backends.kubernetes.KubeBackend"
c.KubeBackend.gateway_instance = config['gateway_service_name']

# ========= Dask Cluster Default Configuration =========
c.KubeClusterConfig.image = f"{config['cluster-image']['name']}:{config['cluster-image']['tag']}"
c.KubeClusterConfig.image_pull_policy = config['cluster']['image_pull_policy']
c.KubeClusterConfig.environment = config['cluster']['environment']

c.KubeClusterConfig.scheduler_cores = config['cluster']['scheduler_cores']
c.KubeClusterConfig.scheduler_cores_limit = config['cluster']['scheduler_cores_limit']
c.KubeClusterConfig.scheduler_memory = config['cluster']['scheduler_memory']
c.KubeClusterConfig.scheduler_memory_limit = config['cluster']['scheduler_memory_limit']
c.KubeClusterConfig.scheduler_extra_container_config = config['cluster']['scheduler_extra_container_config']
c.KubeClusterConfig.scheduler_extra_pod_config = config['cluster']['scheduler_extra_pod_config']

c.KubeClusterConfig.worker_cores = config['cluster']['worker_cores']
c.KubeClusterConfig.worker_cores_limit = config['cluster']['worker_cores_limit']
c.KubeClusterConfig.worker_memory = config['cluster']['worker_memory']
c.KubeClusterConfig.worker_memory_limit = config['cluster']['worker_memory_limit']
c.KubeClusterConfig.worker_extra_container_config = config['cluster']['worker_extra_container_config']
c.KubeClusterConfig.worker_extra_pod_config = config['cluster']['worker_extra_pod_config']



def get_packages(conda_prefix):
    packages = set()
    for filename in os.listdir(os.path.join(conda_prefix, 'conda-meta')):
        if filename.endswith('.json'):
            with open(os.path.join(conda_prefix, 'conda-meta', filename)) as f:
                packages.add(json.load(f).get('name'))
    return packages


def get_conda_prefixes(conda_store_mount):
    for namespace in os.listdir(conda_store_mount):
        if os.path.isdir(os.path.join(conda_store_mount, namespace, 'envs')):
            for name in os.listdir(os.path.join(conda_store_mount, namespace, 'envs')):
                yield namespace, name, os.path.join(conda_store_mount, namespace, 'envs', name)


def list_dask_environments(conda_store_mount):
    for namespace, name, conda_prefix in get_conda_prefixes(conda_store_mount):
        if {'dask', 'distributed'} <= get_packages(conda_prefix):
            yield namespace, name, conda_prefix


def worker_profile(options):
    print(options.profile)
    _config = config['profiles'][options.profile]
    _config['worker_cmd'] = '/opt/conda-run-worker'
    _config['scheduler_cmd'] = '/opt/conda-run-scheduler'
    _config['environment'] = {
        **options.environment_vars,
        'CONDA_ENVIRONMENT': options.conda_environment
    }
    return _config


def user_options(user):
    allowed_namespaces = set(['filesystem', 'default', user.name] + list(user.groups))
    environments = {
        f"{namespace}/{name}": conda_prefix for namespace, name, conda_prefix in list_dask_environments(config['conda-store-mount']) if namespace in allowed_namespaces
    }

    return Options(
        Select(
            "conda_environment",
            list(environments.keys()),
            default=list(environments.keys())[0],
            label='Environment',
        ),
        Select(
            "profile",
            list(config['profiles'].keys()),
            default=list(config['profiles'].keys())[0],
            label="Cluster Profile",
        ),
        Mapping("environment_vars", {}, label="Environment Variables"),
        handler=worker_profile,
    )


c.Backend.cluster_options = user_options


# ============ Authentication =================
class QHubAuthentication(JupyterHubAuthenticator):
    async def authenticate(self, request):
        user = await super().authenticate(request)
        url = f"{self.jupyterhub_api_url}/users/{user.name}"
        kwargs = {
            "headers": {"Authorization": "token %s" % self.jupyterhub_api_token},
            "ssl": self.ssl_context,
        }
        resp = await self.session.get(url, **kwargs)
        data = (await resp.json())['auth_state']['oauth_user']

        if 'dask_gateway_developer' not in data['roles'] and 'dask_gateway_admin' not in data['roles']:
            raise web.HTTPInternalServerError(
                reason="Permission failure user does not have required dask_gateway roles"
            )

        user.admin = 'dask_gateway_admin' in data['roles']
        user.groups = [os.path.basename(group) for group in data['groups'] if os.path.dirname(group) == '/projects']
        return user


# ========= Authentication ==========
c.DaskGateway.authenticator_class = QHubAuthentication
c.JupyterHubAuthenticator.jupyterhub_api_url = config['jupyterhub_api_url']
c.JupyterHubAuthenticator.jupyterhub_api_token = config['jupyterhub_api_token']
