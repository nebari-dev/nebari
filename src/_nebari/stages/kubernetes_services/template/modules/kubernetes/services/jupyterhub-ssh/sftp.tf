resource "kubernetes_secret" "jupyterhub-sftp" {
  metadata {
    name      = "${var.name}-jupyterhub-sftp"
    namespace = var.namespace
  }

  data = {
    "hostKey" = tls_private_key.main.private_key_pem
    "hubUrl"  = var.jupyterhub_api_url
  }
}


resource "kubernetes_service" "jupyterhub-sftp" {
  metadata {
    name      = "${var.name}-jupyterhub-sftp"
    namespace = var.namespace
  }

  spec {
    selector = {
      "app.kubernetes.io/component" = "jupyterhub-sftp"
    }

    port {
      name        = "sftp"
      protocol    = "TCP"
      port        = 8023
      target_port = "sftp"
    }

    type = "ClusterIP"
  }
}


resource "kubernetes_deployment" "jupyterhub-sftp" {
  metadata {
    name      = "${var.name}-jupyterhub-sftp"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        "app.kubernetes.io/component" = "jupyterhub-sftp"
      }
    }

    template {
      metadata {
        labels = {
          "app.kubernetes.io/component" = "jupyterhub-sftp"
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
          name = "home"
          persistent_volume_claim {
            claim_name = var.persistent_volume_claim.name
          }
        }

        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.jupyterhub-ssh.metadata.0.name
          }
        }

        volume {
          name = "secrets"
          secret {
            secret_name  = kubernetes_secret.jupyterhub-sftp.metadata.0.name
            default_mode = "0600"
          }
        }

        container {
          name              = "jupyterhub-sftp"
          image             = "${var.jupyterhub-sftp-image.name}:${var.jupyterhub-sftp-image.tag}"
          image_pull_policy = "Always"

          security_context {
            privileged = true
          }

          volume_mount {
            name       = "home"
            mount_path = "/mnt/home"
            sub_path   = "home"
          }

          volume_mount {
            name       = "config"
            mount_path = "/etc/jupyterhub-ssh/config"
            read_only  = true
          }

          volume_mount {
            name       = "secrets"
            mount_path = "/etc/jupyterhub-sftp/config"
            read_only  = true
          }

          port {
            name           = "sftp"
            container_port = 22
            protocol       = "TCP"
          }
        }
      }
    }
  }
  lifecycle {
    replace_triggered_by = [
      null_resource.pvc,
    ]
  }
}

# hack to force the deployment to update when the pvc changes
resource "null_resource" "pvc" {
  triggers = {
    pvc = var.persistent_volume_claim.id
  }
}
