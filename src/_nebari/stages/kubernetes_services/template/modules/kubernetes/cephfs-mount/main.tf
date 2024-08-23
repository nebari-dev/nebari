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
        storage = "${var.fs_capacity}Gi"
      }
    }
  }

  # Hack to avoid timeout while CephCluster is being created
  timeouts {
    create = "10m"
  }
}
