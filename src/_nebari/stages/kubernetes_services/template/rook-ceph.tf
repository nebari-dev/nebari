# ======================= VARIABLES ======================
variable "rook_ceph_storage_class_name" {
  description = "Name of the storage class to create"
  type        = string
}

locals {
  jhub_storage_length  = length(var.jupyterhub-shared-storage)
  conda_storage_length = length(var.conda-store-filesystem-storage)
  enable-ceph-cluster  = local.jupyterhub-fs == "cephfs" || local.conda-store-fs == "cephfs"
}
# ====================== RESOURCES =======================
module "rook-ceph" {
  count     = local.enable-ceph-cluster ? 1 : 0
  source    = "./modules/kubernetes/services/rook-ceph"
  namespace = var.environment

  storage_class_name    = var.rook_ceph_storage_class_name
  node_group            = var.node_groups.general
  ceph_storage_capacity = tonumber(substr(var.jupyterhub-shared-storage, 0, local.jhub_storage_length - 2)) + tonumber(substr(var.conda-store-filesystem-storage, 0, local.conda_storage_length - 2))

  depends_on = [helm_release.rook-ceph]
}

resource "kubernetes_namespace" "rook-ceph" {
  metadata {
    name = "rook-ceph" # TODO: Make this a variable
  }
}

resource "helm_release" "rook-ceph" {
  name       = "rook-ceph"
  namespace  = "rook-ceph" # var.namespace  # TODO: Consider putting this in deployment namespace
  repository = "https://charts.rook.io/release"
  chart      = "rook-ceph"
  version    = "v1.14.7"

  values = concat([
    file("./modules/kubernetes/services/rook-ceph/operator-values.yaml"),
    jsonencode({
      nodeSelector = {
        "${var.node_groups.general.key}" = var.node_groups.general.value
      },
      monitoring = {
        enabled = false # TODO: Enable monitoring when nebari-config.yaml has it enabled
      },
      csi = {
        enableRbdDriver = false, # necessary to provision block storage, but saves some cpu and memory if not needed
      },
    })
    ],
    # var.overrides
  )

  depends_on = [kubernetes_namespace.rook-ceph]
}
