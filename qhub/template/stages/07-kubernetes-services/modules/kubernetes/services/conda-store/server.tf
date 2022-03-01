resource "kubernetes_config_map" "conda-store-config" {
  metadata {
    name      = "conda-store-config"
    namespace = var.namespace
  }

  data = {
    "conda_store_config.py" = templatefile(
      "${path.module}/config/conda_store_config.py", {
        external-url   = var.external-url
        minio-username = module.minio.root_username
        minio-password = module.minio.root_password
        minio-service  = module.minio.service
        postgres-username = module.postgresql.root_username
        postgres-password = module.postgresql.root_password
        postgres-service  = module.postgresql.service
        openid-config     = module.conda-store-openid-client.config
      })
  }
}


module "conda-store-openid-client" {
  source = "../keycloak-client"

  realm_id     = var.realm_id
  client_id  = "conda_store"
  external-url = var.external-url
  role_mapping = {
    "admin" = ["conda_store_admin"]
    "developer" = ["conda_store_developer"]
    "analyst" = ["conda_store_developer"]
  }
  callback-url-paths = [
    "https://${var.external-url}/conda-store/oauth_callback"
  ]
}


resource "kubernetes_service" "server" {
  metadata {
    name      = "${var.name}-conda-store-server"
    namespace = var.namespace
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
          image = "${var.conda-store-image.name}:${var.conda-store-image.tag}"

          args = [
            "conda-store-server",
            "--config",
            "/etc/conda-store/conda_store_config.py"
          ]

          volume_mount {
            name       = "config"
            mount_path = "/etc/conda-store"
          }
        }

        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.conda-store-config.metadata.0.name
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
