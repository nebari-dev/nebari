module "forwardauth-openid-client" {
  source = "../services/keycloak-client"

  realm_id     = var.realm_id
  client_id    = "forwardauth"
  external-url = var.external-url
  callback-url-paths = [
    "https://${var.external-url}${var.callback-url-path}"
  ]
}


resource "kubernetes_service" "forwardauth-service" {
  metadata {
    name      = "forwardauth-service"
    namespace = var.namespace
  }
  spec {
    selector = {
      app = kubernetes_deployment.forwardauth-deployment.spec.0.template.0.metadata[0].labels.app
    }
    port {
      port        = 4181
      target_port = 4181
    }

    type = "ClusterIP"
  }
}

resource "random_password" "forwardauth_cookie_secret" {
  length  = 32
  special = false
}

resource "kubernetes_deployment" "forwardauth-deployment" {
  metadata {
    name      = "forwardauth-deployment"
    namespace = var.namespace
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "forwardauth-pod"
      }
    }

    template {
      metadata {
        labels = {
          app = "forwardauth-pod"
        }
      }

      spec {
        node_selector = {
          "${var.node-group.key}" = var.node-group.value
        }
        dynamic "volume" {
          for_each = var.cert_secret_name == null ? [] : [1]
          content {
            name = "cert-volume"
            secret {
              secret_name = var.cert_secret_name
              items {
                key  = "tls.crt"
                path = "tls.crt"
              }
            }
          }
        }
        container {
          # image = "thomseddon/traefik-forward-auth:2.2.0"
          # Use PR #159 https://github.com/thomseddon/traefik-forward-auth/pull/159
          image = "maxisme/traefik-forward-auth:sha-a98e568"
          name  = "forwardauth-container"

          env {
            name  = "USER_ID_PATH"
            value = "preferred_username"
          }

          env {
            name  = "PROVIDERS_GENERIC_OAUTH_AUTH_URL"
            value = module.forwardauth-openid-client.config.authentication_url
          }

          env {
            name  = "PROVIDERS_GENERIC_OAUTH_TOKEN_URL"
            value = module.forwardauth-openid-client.config.token_url
          }

          env {
            name  = "PROVIDERS_GENERIC_OAUTH_USER_URL"
            value = module.forwardauth-openid-client.config.userinfo_url
          }

          env {
            name  = "PROVIDERS_GENERIC_OAUTH_CLIENT_ID"
            value = module.forwardauth-openid-client.config.client_id
          }

          env {
            name  = "PROVIDERS_GENERIC_OAUTH_CLIENT_SECRET"
            value = module.forwardauth-openid-client.config.client_secret
          }

          env {
            name  = "SECRET"
            value = random_password.forwardauth_cookie_secret.result
          }

          env {
            name  = "DEFAULT_PROVIDER"
            value = "generic-oauth"
          }

          env {
            name  = "URL_PATH"
            value = var.callback-url-path
          }

          env {
            name  = "LOG_LEVEL"
            value = "trace"
          }
          env {
            name  = "AUTH_HOST"
            value = var.external-url
          }

          env {
            name  = "COOKIE_DOMAIN"
            value = var.external-url
          }

          dynamic "env" {
            for_each = var.cert_secret_name == null ? [] : [1]
            content {
              name  = "SSL_CERT_FILE"
              value = "/config/tls.crt"
            }
          }

          port {
            container_port = 4181
          }

          dynamic "volume_mount" {
            for_each = var.cert_secret_name == null ? [] : [1]
            content {
              name       = "cert-volume"
              mount_path = "/config"
              read_only  = true
            }
          }
        }

      }
    }
  }
}

resource "kubernetes_manifest" "forwardauth-middleware" {
  # This version of the middleware is primarily for the forwardauth service
  # itself, so the callback _oauth url can be centalised (not just under for example /someservice/_oauth).
  # This middleware is in the root namespace, someservice may have its own.
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = var.forwardauth_middleware_name
      namespace = var.namespace
    }
    spec = {
      forwardAuth = {
        address = "http://${kubernetes_service.forwardauth-service.metadata.0.name}:4181"
        authResponseHeaders = [
          "X-Forwarded-User"
        ]
      }
    }
  }
}

resource "kubernetes_manifest" "forwardauth-ingressroute" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "forwardauth"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && PathPrefix(`${var.callback-url-path}`)"

          middlewares = [
            {
              name      = kubernetes_manifest.forwardauth-middleware.manifest.metadata.name
              namespace = var.namespace
            }
          ]

          services = [
            {
              name = kubernetes_service.forwardauth-service.metadata.0.name
              port = 4181
            }
          ]
        }
      ]
    }
  }
}
