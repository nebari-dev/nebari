# ======================= VARIABLES ======================
variable "rook_ceph_storage_class_name" {
  description = "Name of the storage class to create"
  type        = string
}


# ====================== RESOURCES =======================
module "rook-ceph" {
  # count = var.argo-workflows-enabled ? 1 : 0

  source    = "./modules/kubernetes/services/rook-ceph"
  namespace = var.environment

  storage_class_name = var.rook_ceph_storage_class_name
  node_group         = var.node_groups.general
  # external-url = var.endpoint
  # overrides = var.rook-ceph-overrides
}
