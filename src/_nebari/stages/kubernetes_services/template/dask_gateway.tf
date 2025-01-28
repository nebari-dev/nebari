# ===================== VARIABLES ====================
variable "dask-worker-image" {
  description = "Dask worker image"
  type = object({
    name = string
    tag  = string
  })
}

variable "dask-gateway-profiles" {
  description = "Dask Gateway profiles to expose to user"
}

variable "worker-taint-tolerations" {
  description = "Tolerations for the worker node taints needed by Dask Scheduler/Worker pods"
  type = list(object({
    key      = string
    operator = string
    value    = string
    effect   = string
  }))
}

# =================== RESOURCES =====================
module "dask-gateway" {
  source = "./modules/kubernetes/services/dask-gateway"

  namespace            = var.environment
  jupyterhub_api_token = module.jupyterhub.services.dask-gateway.api_token
  jupyterhub_api_url   = "${module.jupyterhub.internal_jupyterhub_url}/hub/api"

  external-url = var.endpoint

  cluster-image = var.dask-worker-image

  general-node-group = var.node_groups.general
  worker-node-group  = var.node_groups.worker

  # needs to match name in module.jupyterhub.extra-mounts
  dask-etc-configmap-name = "dask-etc"

  # environments
  conda-store-pvc               = module.kubernetes-conda-store-server.pvc
  conda-store-mount             = "/home/conda"
  default-conda-store-namespace = var.conda-store-default-namespace
  conda-store-api-token         = module.kubernetes-conda-store-server.service-tokens.dask-gateway
  conda-store-service-name      = module.kubernetes-conda-store-server.service_name

  # profiles
  profiles = var.dask-gateway-profiles

  cloud-provider = var.cloud-provider

  forwardauth_middleware_name = var.forwardauth_middleware_name

  cluster = {
    scheduler_extra_pod_config = {
      tolerations = var.worker-taint-tolerations
    }
    worker_extra_pod_config = {
      tolerations = var.worker-taint-tolerations
    }
  }

  depends_on = [
    module.kubernetes-nfs-server,
    module.rook-ceph
  ]
}
