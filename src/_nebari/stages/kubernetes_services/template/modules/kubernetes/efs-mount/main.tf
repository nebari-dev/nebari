resource "kubernetes_persistent_volume_claim" "main" {
  metadata {
    name      = var.efs-pvc-name
    namespace = var.namespace
  }

  spec {
    access_modes       = ["ReadWriteMany"]
    storage_class_name = "efs-dynamic-retain" # kubernetes_storage_class.main.metadata.0.name  # Get this from a terraform output
    resources {
      requests = {
        storage = "${var.fs_capacity}Gi"
      }
    }
  }

}
