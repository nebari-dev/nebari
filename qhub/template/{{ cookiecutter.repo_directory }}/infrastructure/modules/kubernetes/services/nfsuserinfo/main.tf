resource "kubernetes_service" "main" {
  metadata {
    name      = "qhub-userinfo"
    namespace = var.namespace
  }

  spec {
    selector = {
      role = "qhub-userinfo"
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
    name      = "qhub-userinfo"
    namespace = var.namespace
    labels = {
      role = "qhub-userinfo"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        role = "qhub-userinfo"
      }
    }

    template {
      metadata {
        labels = {
          role = "qhub-userinfo"
        }
      }

      spec {
        container {
          name  = "userinfo"
          image = "danlester/qhub-userinfo:3"

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

          volume_mount {
            name       = "nfs-mount"
            mount_path = "/etc/userinfo-state"
            sub_path   = "userinfo-state"
            read_only  = false
          }
        }

        volume {
          name = "migration"
          config_map {
            name = "qhub-userinfo-migration"
          }
        }

        volume {
          name = "nfs-mount"
        }

      }
    }
  }
}