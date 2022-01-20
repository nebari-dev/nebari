import os
import json

c.DaskGateway.log_level = "${gateway.loglevel}"

# Configure addresses
c.DaskGateway.address = ":8000"
c.KubeBackend.api_url = 'http://{gateway_service_name}.{gateway_service_namespace}:8000/api'

c.DaskGateway.backend_class = "dask_gateway_server.backends.kubernetes.KubeBackend"
c.KubeBackend.gateway_instance = "${gateway_service_name}"

# ========= Authentication ==========
c.DaskGateway.authenticator_class = "dask_gateway_server.auth.JupyterHubAuthenticator"
c.JupyterHubAuthenticator.jupyterhub_api_url = "${jupyterhub_api_url}"

# ========= Dask Cluster Default Configuration =========
c.KubeClusterConfig.image = "${cluster-image.name}:${cluster-image.tag}"
c.KubeClusterConfig.image_pull_policy = "${cluster.image_pull_policy}"
c.KubeClusterConfig.environment = json.loads("${jsonencode(cluster.environment)}")

c.KubeClusterConfig.scheduler_cores = ${cluster.scheduler_cores}
c.KubeClusterConfig.scheduler_cores_limit = ${cluster.scheduler_cores_limit}
c.KubeClusterConfig.scheduler_memory = "${cluster.scheduler_memory}"
c.KubeClusterConfig.scheduler_memory_limit = "${cluster.scheduler_memory_limit}"
c.KubeClusterConfig.scheduler_extra_container_config = json.loads('${jsonencode(cluster.scheduler_extra_container_config)}')
c.KubeClusterConfig.scheduler_extra_pod_config = json.loads('${jsonencode(cluster.scheduler_extra_pod_config)}')

c.KubeClusterConfig.worker_cores = ${cluster.worker_cores}
c.KubeClusterConfig.worker_cores_limit = ${cluster.worker_cores_limit}
c.KubeClusterConfig.worker_memory = "${cluster.worker_memory}"
c.KubeClusterConfig.worker_memory_limit = "${cluster.worker_memory_limit}"
c.KubeClusterConfig.worker_extra_container_config = json.loads('${jsonencode(cluster.worker_extra_container_config)}')
c.KubeClusterConfig.worker_extra_pod_config = json.loads('${jsonencode(cluster.worker_extra_pod_config)}')

# ==========================================
# ========== EXTRA CONFIGURATION ===========
# ==========================================
${extra_config}
