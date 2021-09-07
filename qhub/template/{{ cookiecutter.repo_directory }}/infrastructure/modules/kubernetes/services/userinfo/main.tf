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
      name        = "http"
      port        = 8091
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
          image = "danlester/qhub-userinfo:6"

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

          env {
            name  = "KEYCLOAK_SERVER_URL"
            value = var.keycloak_server_url
          }

          env {
            name  = "KEYCLOAK_USERNAME"
            value = var.keycloak_username
          }

          env {
            name  = "KEYCLOAK_PASSWORD"
            value = var.keycloak_password
          }

        }

      }
    }
  }
}