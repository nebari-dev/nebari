# ======================= VARIABLES ======================
variable "conda-store-environments" {
  description = "Conda-Store managed environments"
  default = {}
}

variable "conda-store-filesystem-storage" {
  description = "Conda-Store storage in GB for filesystem environments that are built"
  type        = string
}

variable "conda-store-object-storage" {
  description = "Conda-Store storage in GB for object storage. Conda-Store uses minio for object storage to be cloud agnostic. If empty default is var.conda-store-filesystem-storage value"
  type        = string
  default     = null
}

variable "conda-store-image" {
  description = "Conda-store image"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "quansight/conda-store-server"
    tag  = "v0.3.15"
  }
}

# ====================== RESOURCES =======================
module "kubernetes-conda-store-server" {
  source = "./modules/kubernetes/services/conda-store"

  name              = "qhub"
  namespace         = var.environment

  external-url = var.endpoint
  realm_id     = var.realm_id

  nfs_capacity      = var.conda-store-filesystem-storage
  minio_capacity    = coalesce(var.conda-store-object-storage, var.conda-store-filesystem-storage)
  node-group        = var.node_groups.general
  conda-store-image = var.conda-store-image
  environments      = {
    for filename, environment in var.conda-store-environments:
    filename => yamlencode(environment)
  }
}

module "conda-store-nfs-mount" {
  source = "./modules/kubernetes/nfs-mount"

  name         = "conda-store"
  namespace    = var.environment
  nfs_capacity = var.conda-store-filesystem-storage
  nfs_endpoint = module.kubernetes-conda-store-server.endpoint_ip

  depends_on = [
    module.kubernetes-conda-store-server
  ]
}
