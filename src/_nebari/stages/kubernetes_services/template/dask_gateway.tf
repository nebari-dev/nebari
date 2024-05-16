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

variable "worker-images" {
  description = "Worker images list options to use for dask-gateway"
  type        = map(string)
  default     = {}
}

variable "extra-worker-mounts" {
  description = "Extra volumes and volume mounts to add to worker pods"
  type        = object({
    volumes = list(any)
    volume_mounts = list(any)
  })
  default = {}
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

  worker-images = var.worker-images
  extra-worker-mounts = var.extra-worker-mounts

  # environments
  conda-store-pvc               = module.conda-store-nfs-mount.persistent_volume_claim.name
  conda-store-mount             = "/home/conda"
  default-conda-store-namespace = var.conda-store-default-namespace
  conda-store-api-token         = module.kubernetes-conda-store-server.service-tokens.dask-gateway
  conda-store-service-name      = module.kubernetes-conda-store-server.service_name

  # profiles
  profiles = var.dask-gateway-profiles

  cloud-provider = var.cloud-provider
}
