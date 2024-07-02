resource "random_password" "conda_store_service_token" {
  for_each = var.services

  length  = 32
  special = false
}

resource "kubernetes_secret" "conda-store-secret" {
  metadata {
    name      = "conda-store-secret"
    namespace = var.namespace
  }

  data = {
    "config.json" = jsonencode({
      external-url           = var.external-url
      minio-username         = module.minio.root_username
      minio-password         = module.minio.root_password
      minio-service          = module.minio.service
      redis-password         = module.redis.root_password
      redis-service          = module.redis.service
      postgres-username      = module.postgresql.root_username
      postgres-password      = module.postgresql.root_password
      postgres-service       = module.postgresql.service
      openid-config          = module.conda-store-openid-client.config
      extra-settings         = var.extra-settings
      extra-config           = var.extra-config
      default-namespace      = var.default-namespace-name
      token_url_internal     = "http://keycloak-http.${var.namespace}.svc/auth/realms/${var.realm_id}/protocol/openid-connect/token"
      realm_api_url_internal = "http://keycloak-http.${var.namespace}.svc/auth/admin/realms/${var.realm_id}"
      service-tokens = {
        for service, value in var.services : base64encode(random_password.conda_store_service_token[service].result) => value
      }
      # So that the mapping can be used in conda-store config itself
      service-tokens-mapping = {
        for service, _ in var.services : service => base64encode(random_password.conda_store_service_token[service].result)
      }
      extra-settings = var.extra-settings
      extra-config   = var.extra-config
    })
  }
}


resource "kubernetes_config_map" "conda-store-config" {
  metadata {
    name      = "conda-store-config"
    namespace = var.namespace
  }

  data = {
    "conda_store_config.py" = file("${path.module}/config/conda_store_config.py")
  }
}


module "conda-store-openid-client" {
  source = "../keycloak-client"

  realm_id     = var.realm_id
  client_id    = "conda_store"
  external-url = var.external-url
  role_mapping = {
    "superadmin" = ["conda_store_superadmin"]
    "admin"      = ["conda_store_admin"]
    "developer"  = ["conda_store_developer"]
    "analyst"    = ["conda_store_developer"]
  }
  callback-url-paths = [
    "https://${var.external-url}/conda-store/oauth_callback"
  ]
  service-accounts-enabled = true
  service-account-roles = [
    "view-realm", "view-users", "view-clients"
  ]
}


resource "kubernetes_service" "server" {
  metadata {
    name      = "${var.name}-conda-store-server"
    namespace = var.namespace
    labels = {
      app       = "conda-store"
      component = "conda-store-server"
    }
  }

  spec {
    selector = {
      role = "${var.name}-conda-store-server"
    }

    port {
      name = "conda-store-server"
      port = 5000
    }
  }
}


resource "kubernetes_deployment" "server" {
  metadata {
    name      = "${var.name}-conda-store-server"
    namespace = var.namespace
    labels = {
      role = "${var.name}-conda-store-server"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        role = "${var.name}-conda-store-server"
      }
    }

    template {
      metadata {
        labels = {
          role = "${var.name}-conda-store-server"
        }

        annotations = {
          # This lets us autorestart when the config changes!
          "checksum/config-map" = sha256(jsonencode(kubernetes_config_map.conda-store-config.data))
          "checksum/secret"     = sha256(jsonencode(kubernetes_secret.conda-store-secret.data))
        }
      }

      spec {
        affinity {
          node_affinity {
            required_during_scheduling_ignored_during_execution {
              node_selector_term {
                match_expressions {
                  key      = var.node-group.key
                  operator = "In"
                  values = [
                    var.node-group.value
                  ]
                }
              }
            }
          }
        }

        container {
          name  = "conda-store-server"
          image = "${var.conda-store-image}:${var.conda-store-image-tag}"

          args = [
            "conda-store-server",
            "--config",
            "/etc/conda-store/conda_store_config.py"
          ]

          volume_mount {
            name       = "config"
            mount_path = "/etc/conda-store"
          }

          volume_mount {
            name       = "secret"
            mount_path = "/var/lib/conda-store/"
          }

          volume_mount {
            name       = "home-volume"
            mount_path = "/home/conda"
          }
        }

        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.conda-store-config.metadata.0.name
          }
        }

        volume {
          name = "secret"
          secret {
            secret_name = kubernetes_secret.conda-store-secret.metadata.0.name
          }
        }

        volume {
          name = "home-volume"
          empty_dir {
            size_limit = "1Mi"
          }
        }
      }
    }
  }
}


resource "kubernetes_manifest" "jupyterhub" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "conda-store-server"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && PathPrefix(`/conda-store`)"
          services = [
            {
              name = kubernetes_service.server.metadata.0.name
              port = 5000
            }
          ]
        }
      ]
    }
  }
}
