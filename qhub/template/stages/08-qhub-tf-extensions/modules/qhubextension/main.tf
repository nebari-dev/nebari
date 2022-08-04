terraform {
  required_providers {
    keycloak = {
      source  = "mrparkers/keycloak"
      version = "3.7.0"
    }
  }
}

resource "kubernetes_service" "qhub-extension-service" {
  metadata {
    name      = "${var.name}-service"
    namespace = var.namespace
  }
  spec {
    selector = {
      app = kubernetes_deployment.qhub-extension-deployment.spec.0.template.0.metadata[0].labels.app
    }
    port {
      port        = 80
      target_port = 80
    }

    type = "ClusterIP"
  }
}

resource "kubernetes_deployment" "qhub-extension-deployment" {
  metadata {
    name      = "${var.name}-deployment"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "${var.name}-pod"
      }
    }

    template {
      metadata {
        labels = {
          app = "${var.name}-pod"
        }
      }

      spec {

        container {
          name  = "${var.name}-container"
          image = var.image

          env {
            name  = "PORT"
            value = "80"
          }

          dynamic "env" {
            for_each = concat(local.oauth2client_envs, local.keycloakadmin_envs, local.jwt_envs, var.envs)
            content {
              name  = env.value["name"]
              value = env.value["value"]
            }
          }

          port {
            container_port = 80
          }

          dynamic "volume_mount" {
            for_each = var.qhubconfigyaml ? [true] : []
            content {
              name       = "qhubyamlsecret"
              mount_path = "/etc/qhubyamlsecret/"
              read_only  = true
            }
          }

        }

        dynamic "volume" {
          for_each = var.qhubconfigyaml ? [true] : []
          content {
            name = "qhubyamlsecret"
            secret {
              secret_name = "qhub-config-yaml"
            }
          }
        }

      }
    }
  }
}

resource "random_password" "qhub-jwt-secret" {
  count   = var.jwt ? 1 : 0
  length  = 32
  special = false
}
