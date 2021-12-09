resource "kubernetes_config_map" "conda-store-config" {
  metadata {
    name      = "conda-store-config"
    namespace = var.namespace
  }

  "conda-store-config.py" = file("${path.module}/config/conda-store-config.py")
}


resource "kubernetes_service" "server" {
  metadata {
    name      = "${var.name}-conda-store-server"
    namespace = var.namespace
  }

  spec {
    selector = {
      role = "${var.name}-conda-store-server"
    }

    port {
      name = "conda-store-server"
      port = 5000
    }
  }
}


resource "kubernetes_deployment" "main" {
  metadata {
    name      = "${var.name}-conda-store-server"
    namespace = var.namespace
    labels = {
      role = "${var.name}-conda-store-server"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        role = "${var.name}-conda-store-server"
      }
    }

    template {
      metadata {
        labels = {
          role = "${var.name}-conda-store-server"
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
          name  = "conda-store-server"
          image = "${var.conda-store-image.name}:${var.conda-store-image.tag}"

          command = [
            - "conda-store-server"
            - "--config"
            - "/etc/conda-store/conda_store_config.py"
          ]

          volume_mount {
            name       = "config"
            mount_path = "/etc/conda-store"
          }
        }

        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.conda-store-config.metadata.0.name
          }
        }
      }
    }
  }
}
