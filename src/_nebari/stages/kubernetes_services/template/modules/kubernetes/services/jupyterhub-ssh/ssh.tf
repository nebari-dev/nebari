resource "tls_private_key" "main" {
  algorithm = "RSA"
  rsa_bits  = 2048
}


resource "kubernetes_config_map" "jupyterhub-ssh" {
  metadata {
    name      = "${var.name}-jupyterhub-ssh"
    namespace = var.namespace
  }

  data = {
    "values.yaml" = <<-EOT
      hubUrl: ${var.jupyterhub_api_url}
      ssh:
        config:
          JupyterHubSSH:
            debug: true
            host_key_path: /etc/jupyterhub-ssh/secrets/jupyterhub-ssh.host-key
    EOT
  }
}


resource "kubernetes_secret" "jupyterhub-ssh" {
  metadata {
    name      = "${var.name}-jupyterhub-ssh"
    namespace = var.namespace
  }

  data = {
    "jupyterhub-ssh.host-key" = tls_private_key.main.private_key_pem
  }
}


resource "kubernetes_service" "jupyterhub-ssh" {
  metadata {
    name      = "${var.name}-jupyterhub-ssh"
    namespace = var.namespace
  }

  spec {
    selector = {
      "app.kubernetes.io/component" = "jupyterhub-ssh"
    }

    port {
      name        = "ssh"
      protocol    = "TCP"
      port        = 8022
      target_port = "ssh"
    }

    type = "ClusterIP"
  }
}


resource "kubernetes_deployment" "jupyterhub-ssh" {
  metadata {
    name      = "${var.name}-jupyterhub-ssh"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "app.kubernetes.io/component" = "jupyterhub-ssh"
      }
    }

    template {
      metadata {
        labels = {
          "app.kubernetes.io/component" = "jupyterhub-ssh"
        }
      }

      spec {
        automount_service_account_token = true

        affinity {
          node_affinity {
            required_during_scheduling_ignored_during_execution {
              node_selector_term {
                match_expressions {
                  key      = var.node-group.key
                  operator = "In"
                  values   = [var.node-group.value]
                }
              }
            }
          }
        }

        volume {
          name = "secrets"
          secret {
            secret_name = kubernetes_secret.jupyterhub-ssh.metadata.0.name
          }
        }

        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.jupyterhub-ssh.metadata.0.name
          }
        }

        container {
          name              = "jupyterhub-ssh"
          image             = "${var.jupyterhub-ssh-image.name}:${var.jupyterhub-ssh-image.tag}"
          image_pull_policy = "Always"

          security_context {
            allow_privilege_escalation = false
            run_as_non_root            = true
            run_as_user                = 1000
          }

          volume_mount {
            name       = "secrets"
            mount_path = "/etc/jupyterhub-ssh/secrets"
            read_only  = true
          }

          volume_mount {
            name       = "config"
            mount_path = "/etc/jupyterhub-ssh/config"
            read_only  = true
          }

          port {
            name           = "ssh"
            container_port = 8022
            protocol       = "TCP"
          }
        }
      }
    }
  }
}
