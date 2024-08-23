resource "kubernetes_storage_class" "main" {
  metadata {
    name = "${var.name}-${var.namespace}-share"
  }
  storage_provisioner = "kubernetes.io/fake-nfs"
}


resource "kubernetes_persistent_volume" "main" {
  metadata {
    name = "${var.name}-${var.namespace}-share"
  }
  spec {
    capacity = {
      storage = "${var.nfs_capacity}Gi"
    }
    storage_class_name = kubernetes_storage_class.main.metadata.0.name
    access_modes       = ["ReadWriteMany"]
    persistent_volume_source {
      nfs {
        path   = "/"
        server = var.nfs_endpoint
      }
    }
  }
}


resource "kubernetes_persistent_volume_claim" "main" {
  metadata {
    name      = var.nfs-pvc-name
    namespace = var.namespace
  }

  spec {
    access_modes       = ["ReadWriteMany"]
    storage_class_name = kubernetes_storage_class.main.metadata.0.name
    resources {
      requests = {
        storage = "${var.nfs_capacity}Gi"
      }
    }
  }
}
