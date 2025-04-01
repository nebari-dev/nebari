# ======================= VARIABLES ======================
variable "shared_fs_id" {
  description = "ID of the shared filesystem"
  type        = string
}

locals {
  enable-efs = local.jupyterhub-fs == "efs" || local.conda-store-fs == "efs"
}
# ====================== RESOURCES =======================
module "efs" {
  count        = local.enable-ceph-cluster ? 1 : 0
  source       = "./modules/kubernetes/services/efs"
  shared_fs_id = var.shared_fs_id
}
