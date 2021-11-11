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

        container {
          # image = "thomseddon/traefik-forward-auth:2.2.0"
          # Use PR #159 https://github.com/thomseddon/traefik-forward-auth/pull/159
          image = "maxisme/traefik-forward-auth:sha-a98e568"
          name  = "forwardauth-container"

          env {
            name  = "USER_ID_PATH"
            value = "name"
          }

          env {
            name  = "PROVIDERS_GENERIC_OAUTH_AUTH_URL"
            value = "https://${var.external-url}/auth/realms/qhub/protocol/openid-connect/auth"
          }

          env {
            name = "PROVIDERS_GENERIC_OAUTH_TOKEN_URL"
            # http://keycloak-headless.${var.namespace}:8080 works fine here actually
            value = "https://${var.external-url}/auth/realms/qhub/protocol/openid-connect/token"
          }

          env {
            name = "PROVIDERS_GENERIC_OAUTH_USER_URL"
            # But http://keycloak-headless.${var.namespace}:8080 does not work here - Token verification failed
            value = "https://${var.external-url}/auth/realms/qhub/protocol/openid-connect/userinfo"
          }

          env {
            name  = "PROVIDERS_GENERIC_OAUTH_CLIENT_ID"
            value = var.jh-client-id
          }

          env {
            name  = "PROVIDERS_GENERIC_OAUTH_CLIENT_SECRET"
            value = var.jh-client-secret
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

          port {
            container_port = 4181
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

  provider = kubernetes-alpha

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "traefik-forward-auth"
      namespace = var.namespace
    }
    spec = {
      forwardAuth = {
        address = "http://forwardauth-service:4181"
        authResponseHeaders = [
          "X-Forwarded-User"
        ]
      }
    }
  }
}
