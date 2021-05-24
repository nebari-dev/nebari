resource "kubernetes_service" "main" {
  metadata {
    name      = "qhub-nfsuserinfo"
    namespace = var.namespace
  }

  spec {
    selector = {
      role = "qhub-nfsuserinfo"
    }

    port {
      name = "http"
      port = 8091
      target_port = 80
    }

  }
}

resource "kubernetes_deployment" "main" {
  metadata {
    name      = "qhub-nfsuserinfo"
    namespace = var.namespace
    labels = {
      role = "qhub-nfsuserinfo"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        role = "qhub-nfsuserinfo"
      }
    }

    template {
      metadata {
        labels = {
          role = "qhub-nfsuserinfo"
        }
      }

      spec {
        container {
          name  = "nfsuserinfo"
          image = "quansight/qhub-nfsuserinfo:1"

          port {
            name           = "http"
            container_port = 80
          }

          env {
            name  = "WEB_CONCURRENCY"
            value = "1"
          }

          env {
            name  = "MAX_WORKERS"
            value = "1"
          }

          volume_mount {
            name       = "migration"
            mount_path = "/etc/migration-state"
            read_only  = true
          }
        }

        volume {
          name = "migration"
          config_map {
            name = "qhub-nfsuserinfo-migration"
          }
        }

      }
    }
  }
}