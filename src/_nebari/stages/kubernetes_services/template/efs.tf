# ======================= VARIABLES ======================
variable "shared_fs_id" {
  description = "ID of the shared filesystem"
  type        = string
  default     = ""
}

locals {
  enable-efs = local.jupyterhub-fs == "efs" || local.conda-store-fs == "efs"
}
# ====================== RESOURCES =======================
module "efs" {
  count        = local.enable-efs ? 1 : 0
  source       = "./modules/kubernetes/efs"
  shared_fs_id = var.shared_fs_id
}
