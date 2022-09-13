# ======================= VARIABLES ======================
variable "conda-store-environments" {
  description = "Conda-Store managed environments"
  default     = {}
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

variable "conda-store-extra-settings" {
  description = "Conda-Store extra traitlet settings to apply in `c.Class.key = value` form"
  type        = map(any)
  default     = {}
}

variable "conda-store-extra-config" {
  description = "Additional traitlets configuration code to be ran"
  type        = string
  default     = ""
}

variable "conda-store-image" {
  description = "Conda-Store image"
  type        = string
  default     = "quansight/conda-store-server"
}

variable "conda-store-image-tag" {
  description = "Version of conda-store to use"
  type        = string
  default     = "v0.4.9"
}

# ====================== RESOURCES =======================
module "kubernetes-conda-store-server" {
  source = "./modules/kubernetes/services/conda-store"

  name      = "qhub"
  namespace = var.environment

  external-url = var.endpoint
  realm_id     = var.realm_id

  nfs_capacity          = var.conda-store-filesystem-storage
  minio_capacity        = coalesce(var.conda-store-object-storage, var.conda-store-filesystem-storage)
  node-group            = var.node_groups.general
  conda-store-image     = var.conda-store-image
  conda-store-image-tag = var.conda-store-image-tag
  environments = {
    for filename, environment in var.conda-store-environments :
    filename => yamlencode(environment)
  }
  services       = var.conda-store-service-token-scopes
  extra-settings = var.conda-store-extra-settings
  extra-config   = var.conda-store-extra-config
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
