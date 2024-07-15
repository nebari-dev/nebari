# resource "kubernetes_storage_class" "main" {
#   metadata {
#     name = "${var.name}-${var.namespace}-share"
#   }
#   storage_provisioner = "kubernetes.io/fake-nfs"
# }


# resource "kubernetes_persistent_volume" "main" {
#   metadata {
#     name = "${var.name}-${var.namespace}-share"
#   }
#   spec {
#     capacity = {
#       storage = var.nfs_capacity
#     }
#     storage_class_name = "ceph-filesystem" #  # kubernetes_storage_class.main.metadata.0.name  # TODO: Get this from a terraform output
#     access_modes       = ["ReadWriteMany"]
#     persistent_volume_source {
#       csi {
#         driver = "rook-ceph.cephfs.csi.ceph.com"
#         volume_handle = "myfs"
#         # fstype = "ext4"
#         volume_attributes = {
#           # "clusterID" = "mycluster"
#           # "path" = "/myfs"
#         }

#       }
#     }
#   }
# }


resource "kubernetes_persistent_volume_claim" "main" {
  metadata {
    name      = "${var.name}-${var.namespace}-share"
    namespace = var.namespace
  }

  spec {
    access_modes       = ["ReadWriteMany"]
    storage_class_name = "ceph-filesystem-retain" # kubernetes_storage_class.main.metadata.0.name  # Get this from a terraform output
    resources {
      requests = {
        storage = var.nfs_capacity
      }
    }
  }
}
