# ===================== VARIABLES ====================
variable "dask-worker-image" {
  description = "Dask worker image"
  type = object({
    name = string
    tag  = string
  })
}

variable "dask-gateway-image" {
  description = "Dask worker image"
  type = object({
    name = string
    tag  = string
  })
}

variable "dask-gateway-profiles" {
  description = "Dask Gateway profiles to expose to user"
  default = []
}


# =================== RESOURCES =====================
module "dask-gateway" {
  source = "./modules/kubernetes/services/dask-gateway"

  namespace            = var.environment
  jupyterhub_api_token = module.jupyterhub.services.dask-gateway.api_token
  jupyterhub_api_url   = "${module.jupyterhub.internal_jupyterhub_url}/hub/api"

  external-url = var.endpoint

  cluster-image    = var.dask-worker-image
  gateway-image    = var.dask-gateway-image
  controller-image = var.dask-gateway-image

  general-node-group = var.node_groups.general
  worker-node-group  = var.node_groups.worker

  # needs to match name in module.jupyterhub.extra-mounts
  dask-etc-configmap-name = "dask-etc"

  # environments
  conda-store-pvc = module.conda-store-nfs-mount.persistent_volume_claim.name
  conda-store-mount = "/home/conda"

  # profiles
  profiles = var.dask-gateway-profiles

  # # default cluster behavior
  # cluster = {
  #   # scheduler configuration
  #   scheduler_cores        = 1
  #   scheduler_cores_limit  = 1
  #   scheduler_memory       = "2 G"
  #   scheduler_memory_limit = "2 G"
  #   scheduler_extra_container_config = {
  #     volumeMounts = [
  #       {
  #         name      = "conda-store"
  #         mountPath = "/home/conda"
  #       }
  #     ]
  #   }
  #   scheduler_extra_pod_config = {
  #     affinity = local.affinity.worker-nodegroup
  #     volumes = [
  #       {
  #         name = "conda-store"
  #         persistentVolumeClaim = {
  #           claimName = var.conda-store-pvc
  #         }
  #       }
  #     ]
  #   }
  #   # worker configuration
  #   worker_cores        = 1
  #   worker_cores_limit  = 1
  #   worker_memory       = "2 G"
  #   worker_memory_limit = "2 G"
  #   worker_extra_container_config = {
  #     volumeMounts = [
  #       {
  #         name      = "conda-store"
  #         mountPath = "/home/conda"
  #       }
  #     ]
  #   }
  #   worker_extra_pod_config = {
  #     affinity = local.affinity.worker-nodegroup
  #     volumes = [
  #       {
  #         name = "conda-store"
  #         persistentVolumeClaim = {
  #           claimName = var.conda-store-pvc
  #         }
  #       }
  #     ]
  #   }
  #   # additional fields
  #   image_pull_policy = "IfNotPresent"
  #   environment       = {}
  # }

  # extra_config = var.dask_gateway_extra_config
}
