resource "kubernetes_persistent_volume_claim" "main" {
  metadata {
    name      = "${var.name}-conda-store-storage"
    namespace = var.namespace
  }
  wait_until_bound = true
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = var.nfs_capacity
      }
    }
  }
}

resource "kubernetes_service" "main" {
  metadata {
    name      = "${var.name}-conda-store"
    namespace = var.namespace
  }

  spec {
    selector = {
      role = "${var.name}-conda-store"
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
    name      = "${var.name}-conda-store"
    namespace = var.namespace
    labels = {
      role = "${var.name}-conda-store"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        role = "${var.name}-conda-store"
      }
    }

    template {
      metadata {
        labels = {
          role = "${var.name}-conda-store"
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
          name  = "conda-store"
          image = "${var.conda-store-image.name}:${var.conda-store-image.tag}"

          command = [
            "python", "/opt/conda-store/conda-store.py",
            "-e", "/opt/environments",
            "-o", "/home/conda/environments",
            "-s", "/home/conda/store",
            "--uid", "0",
            "--gid", "0",
            "--permissions", "775"
          ]

          volume_mount {
            name       = "conda-environments"
            mount_path = "/opt/environments"
          }

          volume_mount {
            mount_path = "/home/conda"
            name       = "nfs-export-fast"
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
            claim_name = "${var.name}-conda-store-storage"
          }
        }

        volume {
          name = "conda-environments"
          config_map {
            name = kubernetes_config_map.conda-environments.metadata.0.name
          }
        }
      }
    }
  }
}

resource "kubernetes_config_map" "conda-environments" {
  metadata {
    name      = "conda-environments"
    namespace = var.namespace
  }

  data = var.environments
}