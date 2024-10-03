locals {
  clients = {
    for client in var.clients : client => client
  }
}

resource "random_password" "backup_restore_service_token" {
  for_each = local.clients
  length   = 32
  special  = false
}

resource "kubernetes_secret" "backup_restore_service_token" {
  for_each = local.clients
  metadata {
    name      = "backup-restore-${each.key}"
    namespace = var.namespace
  }

  data = {
    token = random_password.backup_restore_service_token[each.key].result
  }
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

resource "kubernetes_config_map" "backup-restore-etc" {
  metadata {
    name      = "backup-restore-etc"
    namespace = var.namespace
  }

  data = {
    "keycloak.json" = jsonencode({})
    "storage.json"  = jsonencode({})
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
              name = kubernetes_service.backup_restore.metadata.0.name
              port = 8000
            }
          ]
        }
      ]
    }
  }
}


module "jupyterhub-openid-client" {
  source = "../keycloak-client"

  realm_id                 = var.realm_id
  client_id                = "nebari-cli"
  external-url             = var.external-url
  role_mapping             = {}
  client_roles             = []
  callback-url-paths       = []
  service-accounts-enabled = true
  service-account-roles    = ["realm-admin"]
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
          name              = "backup-restore"
          image             = "${var.backup-restore-image}:${var.backup-restore-image-tag}"
          image_pull_policy = "Always"

          env {
            name  = "CONFIG_DIR"
            value = "/etc/backup-restore/config"
          }

          command = ["backup-restore", "--standalone"]

          volume_mount {
            name       = "config"
            mount_path = "/etc/backup-restore/config"
            read_only  = true
          }

          port {
            container_port = 8000
          }
        }

        volume {
          name = "config"

          config_map {
            name = kubernetes_config_map.backup-restore-etc.metadata.0.name
          }
        }
      }
    }
  }
}
