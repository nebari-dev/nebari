resource "kubernetes_persistent_volume_claim" "main" {
  metadata {
    name      = "${var.name}-nfs-storage"
    namespace = var.namespace
  }

  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = "${var.nfs_capacity}Gi"
      }
    }
  }
}


resource "kubernetes_service" "main" {
  metadata {
    name      = "${var.name}-nfs"
    namespace = var.namespace
  }

  spec {
    selector = {
      role = "${var.name}-nfs"
    }

    port {
      name = "nfs"
      port = 2049
    }

    port {
      name = "mountd"
      port = 20048
    }

    port {
      name = "rpcbind"
      port = 111
    }
  }
}


resource "kubernetes_deployment" "main" {
  metadata {
    name      = "${var.name}-nfs"
    namespace = var.namespace
    labels = {
      role = "${var.name}-nfs"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        role = "${var.name}-nfs"
      }
    }

    template {
      metadata {
        labels = {
          role = "${var.name}-nfs"
        }
      }

      spec {
        affinity {
          node_affinity {
            required_during_scheduling_ignored_during_execution {
              node_selector_term {
                match_expressions {
                  key      = var.node-group.key
                  operator = "In"
                  values = [
                    var.node-group.value
                  ]
                }
              }
            }
          }
        }

        container {
          name  = "nfs-server"
          image = "gcr.io/google_containers/volume-nfs:0.8"

          port {
            name           = "nfs"
            container_port = 2049
          }

          port {
            name           = "mountd"
            container_port = 20048
          }

          port {
            name           = "rpcbind"
            container_port = 111
          }

          security_context {
            privileged = true
          }

          volume_mount {
            mount_path = "/exports"
            name       = "nfs-export-fast"
          }
        }

        volume {
          name = "nfs-export-fast"
          persistent_volume_claim {
            claim_name = "${var.name}-nfs-storage"
          }
        }
      }
    }
  }
}
