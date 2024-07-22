# ======================= VARIABLES ======================
variable "conda-store-environments" {
  description = "Conda-Store managed environments"
}

variable "conda-store-filesystem-storage" {
  description = "Conda-Store storage in GB for filesystem environments that are built"
  type        = string
}

variable "conda-store-object-storage" {
  description = "Conda-Store storage in GB for object storage. Conda-Store uses minio for object storage to be cloud agnostic. If empty default is var.conda-store-filesystem-storage value"
  type        = string
}

variable "conda-store-extra-settings" {
  description = "Conda-Store extra traitlet settings to apply in `c.Class.key = value` form"
  type        = map(any)
}

variable "conda-store-extra-config" {
  description = "Additional traitlets configuration code to be ran"
  type        = string
}

variable "conda-store-image" {
  description = "Conda-Store image"
  type        = string
}

variable "conda-store-image-tag" {
  description = "Version of conda-store to use"
  type        = string
}

variable "conda-store-service-token-scopes" {
  description = "Map of services tokens and scopes for conda-store"
  type        = map(any)
}

# ====================== RESOURCES =======================
module "kubernetes-conda-store-server" {
  source = "./modules/kubernetes/services/conda-store"

  name      = "nebari"
  namespace = var.environment

  external-url = var.endpoint
  realm_id     = var.realm_id

  nfs_capacity           = var.conda-store-filesystem-storage
  minio_capacity         = coalesce(var.conda-store-object-storage, var.conda-store-filesystem-storage)
  node-group             = var.node_groups.general
  conda-store-image      = var.conda-store-image
  conda-store-image-tag  = var.conda-store-image-tag
  default-namespace-name = var.conda-store-default-namespace
  environments = {
    for filename, environment in var.conda-store-environments :
    filename => yamlencode(environment)
  }
  services       = var.conda-store-service-token-scopes
  extra-settings = var.conda-store-extra-settings
  extra-config   = var.conda-store-extra-config

  create-pvc               = local.conda-store-fs == "nfs"
  pvc-name                 = local.conda-store-fs == "nfs" ? local.new-pvc-name : local.conda-store-pvc-name
  enable-nfs-server-worker = local.conda-store-fs == "nfs"

  depends_on = [
    module.conda-store-cephfs-mount
  ]
}

locals {
  conda-store-fs       = var.shared_fs_type
  conda-store-pvc-name = "conda-store-${var.environment}-share"
  new-pvc-name         = "nebari-conda-store-storage"
}

module "conda-store-nfs-mount" {
  count  = local.conda-store-fs == "nfs" ? 1 : 0
  source = "./modules/kubernetes/nfs-mount"

  name         = "conda-store"
  namespace    = var.environment
  nfs_capacity = var.conda-store-filesystem-storage
  nfs_endpoint = module.kubernetes-conda-store-server.endpoint_ip
  nfs-pvc-name = local.conda-store-pvc-name

  depends_on = [
    module.kubernetes-nfs-server,
    module.kubernetes-conda-store-server
  ]
}


module "conda-store-cephfs-mount" {
  count  = local.conda-store-fs == "cephfs" ? 1 : 0
  source = "./modules/kubernetes/cephfs-mount"

  name          = "conda-store"
  namespace     = var.environment
  fs_capacity   = var.conda-store-filesystem-storage
  ceph-pvc-name = local.conda-store-pvc-name

  depends_on = [
    module.rook-ceph,
  ]
}
