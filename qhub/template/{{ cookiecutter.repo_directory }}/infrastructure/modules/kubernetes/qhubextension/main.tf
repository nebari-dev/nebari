terraform {
  required_providers {
    keycloak = {
      source  = "mrparkers/keycloak"
      version = "3.3.0"
    }
  }
}

resource "kubernetes_service" "qhub-extension-service" {
  metadata {
    name      = "${var.name}-qhubext-service"
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
            for_each = var.envs
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
              name       = "qhubyamlconfigmap"
              mount_path = "/etc/qhubyamlconfigmap/"
              read_only  = true
            }
          }

        }

        dynamic "volume" {
          for_each = var.qhubconfigyaml ? [true] : []
          content {
            name = "qhubyamlconfigmap"
            config_map {
              name = "qhub-config-yaml"
            }
          }
        }

      }
    }
  }
}
