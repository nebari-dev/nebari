resource "random_password" "backup_restore_service_token" {
  for_each = var.clients
  length   = 32
  special  = false
}

resource "kubernetes_service" "backup_restore" {
  metadata {
    name      = "backup-restore"
    namespace = var.namespace
  }

  spec {
    selector = {
      app = "backup-restore"
    }

    port {
      port     = 8000
      protocol = "TCP"
    }
  }
}

resource "kubernetes_service_account" "backup_restore" {
  metadata {
    name      = "backup-restore"
    namespace = var.namespace
  }
}

resource "kubernetes_manifest" "backup_restore" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "backup-restore"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && PathPrefix(`/backup-restore/`)"

          middlewares = [
            {
              name      = "nebari-backup-restore-api"
              namespace = var.namespace
            }
          ]

          services = [
            {
              name = kubernetes_service.gateway.metadata.0.name
              port = 8000
            }
          ]
        }
      ]
    }
  }
}

resource "kubernetes_secret" "backup_restore_service_token" {
  for_each = var.clients
  metadata {
    name      = "backup-restore-${each.key}"
    namespace = var.namespace
  }

  data = {
    token = random_password.backup_restore_service_token[each.key].result
  }
}

resource "kubernetes_deployment" "backup_restore" {
  metadata {
    name      = "backup-restore"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "backup-restore"
      }
    }

    template {
      metadata {
        labels = {
          app = "backup-restore"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.backup_restore.metadata.0.name

        container {
          name  = "backup-restore"
          image = "nebari/backup-restore:latest"

          env {
            name  = "BACKUP_RESTORE_TOKEN"
            value = kubernetes_secret.backup_restore_service_token[each.key].data["token"]
          }

          env {
            name  = "BACKUP_RESTORE_NAMESPACE"
            value = var.namespace
          }

          env {
            name  = "BACKUP_RESTORE_EXTERNAL_URL"
            value = var.external-url
          }

          env {
            name  = "BACKUP_RESTORE_CLIENT"
            value = each.key
          }

          port {
            container_port = 8000
          }
        }
      }
    }
  }
}
