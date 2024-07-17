# ======================= VARIABLES ======================
variable "rook_ceph_storage_class_name" {
  description = "Name of the storage class to create"
  type        = string
}

locals {
  jhub_storage_length  = length(var.jupyterhub-shared-storage)
  conda_storage_length = length(var.conda-store-filesystem-storage)
}
# ====================== RESOURCES =======================
module "rook-ceph" {
  # count = var.argo-workflows-enabled ? 1 : 0

  source    = "./modules/kubernetes/services/rook-ceph"
  namespace = var.environment

  storage_class_name    = var.rook_ceph_storage_class_name
  node_group            = var.node_groups.general
  ceph_storage_capacity = tonumber(substr(var.jupyterhub-shared-storage, 0, local.jhub_storage_length - 2)) + tonumber(substr(var.conda-store-filesystem-storage, 0, local.conda_storage_length - 2))

  # external-url = var.endpoint
  # overrides = var.rook-ceph-overrides
}
