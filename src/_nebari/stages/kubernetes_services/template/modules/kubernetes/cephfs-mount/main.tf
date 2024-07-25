# resource "kubernetes_persistent_volume" "main" {
#   metadata {
#     name = "${var.name}-${var.namespace}-share"
#   }
#   spec {
#     capacity = {
#       storage = var.nfs_capacity
#     }
#     storage_class_name = kubernetes_storage_class.main.metadata.0.name
#     access_modes       = ["ReadWriteMany"]
#     persistent_volume_source {
#       csi {
#         # I'm not sure if these are correct
#         driver = "cephfs.csi.ceph.com"
#         volume_handle = "cephfs-volume"
#         volume_attributes = {
#           "clusterID" = "rook-ceph"
#           "path" = "/"
#         }
#       }
#       # nfs {
#       #   path   = "/"
#       #   server = var.nfs_endpoint
#       # }
#     }
#   }
# }


resource "kubernetes_persistent_volume_claim" "main" {
  metadata {
    name      = var.ceph-pvc-name
    namespace = var.namespace
  }

  spec {
    access_modes       = ["ReadWriteMany"]
    storage_class_name = "ceph-filesystem-retain" # kubernetes_storage_class.main.metadata.0.name  # Get this from a terraform output
    resources {
      requests = {
        storage = var.fs_capacity
      }
    }
  }
}
