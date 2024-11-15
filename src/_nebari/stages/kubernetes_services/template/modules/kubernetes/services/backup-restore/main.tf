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

locals {
  clients = {
    for client in var.clients : client => client
  }
  services = {
    "keycloak.json" = jsonencode({
      "auth" : {
        "auth_url" : "https://${var.external-url}/auth",
        "realm" : var.realm_id,
        "client_id" : "nebari-cli",
        "client_secret" : module.jupyterhub-openid-client.client_secret,
        "verify_ssl" : false
      }
    })
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

resource "kubernetes_config_map" "backup-restore-etc" {
  metadata {
    name      = "backup-restore-etc"
    namespace = var.namespace
  }

  # Merge local.services with the storage.json entry
  data = merge(local.services, {
    "storage.json" = jsonencode(var.storage)
  })
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
          image             = "${var.image}:${var.image_tag}"
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
