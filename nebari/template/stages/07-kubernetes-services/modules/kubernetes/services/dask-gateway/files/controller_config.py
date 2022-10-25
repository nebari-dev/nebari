import json


def dask_gateway_config(path="/var/lib/dask-gateway/config.json"):
    with open(path) as f:
        return json.load(f)


config = dask_gateway_config()

c.KubeController.address = ":8000"
c.KubeController.api_url = f'http://{config["gateway_service_name"]}.{config["gateway_service_namespace"]}:8000/api'
c.KubeController.gateway_instance = config["gateway_service_name"]
c.KubeController.proxy_prefix = config["gateway"]["prefix"]
c.KubeController.proxy_web_middlewares = [
    {
        "name": config["gateway_cluster_middleware_name"],
        "namespace": config["gateway_cluster_middleware_namespace"],
    }
]
c.KubeController.log_level = config["controller"]["loglevel"]
c.KubeController.completed_cluster_max_age = config["controller"][
    "completedClusterMaxAge"
]
c.KubeController.completed_cluster_cleanup_period = config["controller"][
    "completedClusterCleanupPeriod"
]
c.KubeController.backoff_base_delay = config["controller"]["backoffBaseDelay"]
c.KubeController.backoff_max_delay = config["controller"]["backoffMaxDelay"]
c.KubeController.k8s_api_rate_limit = config["controller"]["k8sApiRateLimit"]
c.KubeController.k8s_api_rate_limit_burst = config["controller"]["k8sApiRateLimitBurst"]

c.KubeController.proxy_web_entrypoint = "websecure"
c.KubeController.proxy_tcp_entrypoint = "tcp"
