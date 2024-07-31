module "conda-store-nfs-mount" {
  count  = var.conda-store-fs == "nfs" ? 1 : 0
  source = "../../../../modules/kubernetes/nfs-mount"

  name         = "conda-store"
  namespace    = var.namespace
  nfs_capacity = var.nfs_capacity
  nfs_endpoint = kubernetes_service.nfs.spec.0.cluster_ip
  nfs-pvc-name = local.conda-store-pvc-name

  depends_on = [
    kubernetes_deployment.worker,
  ]
}


locals {
  conda-store-pvc-name     = "conda-store-${var.namespace}-share"
  new-pvc-name             = "nebari-conda-store-storage"
  create-pvc               = var.conda-store-fs == "nfs"
  enable-nfs-server-worker = var.conda-store-fs == "nfs"
  pvc-name                 = var.conda-store-fs == "nfs" ? local.new-pvc-name : local.conda-store-pvc-name
  shared-pvc               = var.conda-store-fs == "nfs" ? module.conda-store-nfs-mount[0].persistent_volume_claim.pvc : module.conda-store-cephfs-mount[0].persistent_volume_claim.pvc
}



module "conda-store-cephfs-mount" {
  count  = var.conda-store-fs == "cephfs" ? 1 : 0
  source = "../../../../modules/kubernetes/cephfs-mount"

  name          = "conda-store"
  namespace     = var.namespace
  fs_capacity   = var.nfs_capacity # conda-store-filesystem-storage
  ceph-pvc-name = local.conda-store-pvc-name
}
