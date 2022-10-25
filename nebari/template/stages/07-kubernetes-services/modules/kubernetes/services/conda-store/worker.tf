resource "kubernetes_service" "nfs" {
  metadata {
    name      = "${var.name}-conda-store-nfs"
    namespace = var.namespace
  }

  spec {
    selector = {
      role = "${var.name}-conda-store-worker"
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


resource "kubernetes_persistent_volume_claim" "main" {
  metadata {
    name      = "${var.name}-conda-store-storage"
    namespace = var.namespace
  }

  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = var.nfs_capacity
      }
    }
  }
}


resource "kubernetes_config_map" "conda-store-environments" {
  metadata {
    name      = "conda-environments"
    namespace = var.namespace
  }

  data = var.environments
}


resource "kubernetes_deployment" "worker" {
  metadata {
    name      = "${var.name}-conda-store-worker"
    namespace = var.namespace
    labels = {
      role = "${var.name}-conda-store-worker"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        role = "${var.name}-conda-store-worker"
      }
    }

    template {
      metadata {
        labels = {
          role = "${var.name}-conda-store-worker"
        }

        annotations = {
          # This lets us autorestart when the conifg changes!
          "checksum/config-map"         = sha256(jsonencode(kubernetes_config_map.conda-store-config.data))
          "checksum/secret"             = sha256(jsonencode(kubernetes_secret.conda-store-secret.data))
          "checksum/conda-environments" = sha256(jsonencode(kubernetes_config_map.conda-store-environments.data))
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
          name  = "conda-store-worker"
          image = "${var.conda-store-image}:${var.conda-store-image-tag}"

          args = [
            "conda-store-worker",
            "--config",
            "/etc/conda-store/conda_store_config.py"
          ]

          volume_mount {
            name       = "config"
            mount_path = "/etc/conda-store"
          }

          volume_mount {
            name       = "environments"
            mount_path = "/opt/environments"
          }

          volume_mount {
            name       = "storage"
            mount_path = "/home/conda"
          }

          volume_mount {
            name       = "secret"
            mount_path = "/var/lib/conda-store/"
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
            name       = "storage"
          }
        }

        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.conda-store-config.metadata.0.name
          }
        }

        volume {
          name = "secret"
          secret {
            secret_name = kubernetes_secret.conda-store-secret.metadata.0.name
          }
        }

        volume {
          name = "environments"
          config_map {
            name = kubernetes_config_map.conda-store-environments.metadata.0.name
          }
        }

        volume {
          name = "storage"
          persistent_volume_claim {
            # on AWS the pvc gets stuck in a provisioning state if we
            # directly reference the pvc may no longer be issue in
            # future
            # claim_name = kubernetes_persistent_volume_claim.main.metadata.0.name
            claim_name = "${var.name}-conda-store-storage"
          }
        }
        security_context {
          run_as_group = 0
          run_as_user  = 0
        }
      }
    }
  }
}
