variable "jupyterhub-theme" {
  description = "JupyterHub theme"
  type        = map(any)
}

variable "jupyterhub-image" {
  description = "Jupyterhub user image"
  type = object({
    name = string
    tag  = string
  })
}

variable "jupyterhub-overrides" {
  description = "Jupyterhub helm chart overrides"
  type        = list(string)
  default     = []
}

variable "jupyterhub-shared-storage" {
  description = "JupyterHub shared storage size [GB]"
  type        = string
}

variable "jupyterhub-shared-endpoint" {
  description = "JupyterHub shared storage nfs endpoint"
  type        = string
}

variable "jupyterlab-image" {
  description = "Jupyterlab user image"
  type = object({
    name = string
    tag  = string
  })
}

variable "jupyterlab-profiles" {
  description = "JupyterHub profiles to expose to user"
}

variable "jupyterhub-hub-extraEnv" {
  description = "Extracted overrides to merge with jupyterhub.hub.extraEnv"
  type        = string
  default     = "[]"
}

variable "idle-culler-settings" {
  description = "Idle culler timeout settings (in minutes)"
  type        = any
}


module "kubernetes-nfs-server" {
  count = var.jupyterhub-shared-endpoint == null ? 1 : 0

  source = "./modules/kubernetes/nfs-server"

  name         = "nfs-server"
  namespace    = var.environment
  nfs_capacity = var.jupyterhub-shared-storage
  node-group   = var.node_groups.general
}


module "jupyterhub-nfs-mount" {
  source = "./modules/kubernetes/nfs-mount"

  name         = "jupyterhub"
  namespace    = var.environment
  nfs_capacity = var.jupyterhub-shared-storage
  nfs_endpoint = var.jupyterhub-shared-endpoint == null ? module.kubernetes-nfs-server.0.endpoint_ip : var.jupyterhub-shared-endpoint

  depends_on = [
    module.kubernetes-nfs-server
  ]
}


module "jupyterhub" {
  source = "./modules/kubernetes/services/jupyterhub"

  name      = var.name
  namespace = var.environment

  external-url = var.endpoint
  realm_id     = var.realm_id

  overrides = var.jupyterhub-overrides

  home-pvc = module.jupyterhub-nfs-mount.persistent_volume_claim.name

  shared-pvc = module.jupyterhub-nfs-mount.persistent_volume_claim.name

  conda-store-pvc                                    = module.conda-store-nfs-mount.persistent_volume_claim.name
  conda-store-mount                                  = "/home/conda"
  conda-store-environments                           = var.conda-store-environments
  default-conda-store-namespace                      = var.conda-store-default-namespace
  argo-workflows-enabled                             = var.argo-workflows-enabled
  conda-store-argo-workflows-jupyter-scheduler-token = module.kubernetes-conda-store-server.service-tokens.argo-workflows-jupyter-scheduler
  conda-store-service-name                           = module.kubernetes-conda-store-server.service_name

  extra-mounts = {
    "/etc/dask" = {
      name      = "dask-etc"
      namespace = var.environment
      kind      = "configmap"
    },
  }

  services = concat([
    "dask-gateway"
    ],
    (var.monitoring-enabled ? ["monitoring"] : []),
    (var.prefect-enabled ? ["prefect"] : []),
    (var.kbatch-enabled ? ["kbatch"] : [])
  )

  general-node-group = var.node_groups.general
  user-node-group    = var.node_groups.user

  jupyterhub-image = var.jupyterhub-image
  jupyterlab-image = var.jupyterlab-image

  theme    = var.jupyterhub-theme
  profiles = var.jupyterlab-profiles

  jupyterhub-logout-redirect-url = var.jupyterhub-logout-redirect-url
  jupyterhub-hub-extraEnv        = var.jupyterhub-hub-extraEnv

  idle-culler-settings = var.idle-culler-settings

}
