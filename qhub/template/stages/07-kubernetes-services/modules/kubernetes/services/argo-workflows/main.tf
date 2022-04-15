locals {
  name = "argo-workflows"
  argo-workflows-prefix = "argo"
}

resource "helm_release" "argo-workflows" {
  name       = local.name
  namespace  = var.namespace
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-workflows"
  version    = "0.13.1"

  values = concat([
    file("${path.module}/values.yaml"),
    # https://github.com/argoproj/argo-helm/blob/argo-workflows-0.13.1/charts/argo-workflows/values.yaml


    jsonencode({
      singleNamespace = true  # Restrict Argo to operate only in a single namespace (the namespace of the Helm release)

      controller = {
        metricsConfig = {
          enabled = true  # enable prometheus
        }
        workflowNamespaces = [
          "${var.namespace}"
          ]
      }

      server = {
        # `sso` for OIDC/OAuth
        extraArgs = ["--auth-mode=sso", "--insecure-skip-verify"]
        # to enable TLS, `secure = true`
        secure = false
        baseHref = "/${local.argo-workflows-prefix}/"

        sso = {
          issuer = "https://${var.external-url}/auth/realms/${var.realm_id}"
          clientId = {
            name = "argo-server-sso"
            key = "argo-oidc-client-id"
          }
          clientSecret = {
            name = "argo-server-sso"
            key = "argo-oidc-client-secret"
          }
          # The OIDC redirect URL. Should be in the form <argo-root-url>/oauth2/callback.
          redirectUrl = "https://${var.external-url}/oauth2/callback"
          rbac = {
            enabled = false
            # secretWhitelist = []
          }
          # scopes = ["groups"]
        }
      }

      containerRuntimeExecutor = "emissary"

    })
  ], var.overrides)
}

resource "kubernetes_secret" "argo-oidc-secret" {
  metadata {
    name = "argo-server-sso"
    namespace = var.namespace
  }
  data = {
    "argo-oidc-client-id"     = module.argo-workflow-openid-client.config.client_id
    "argo-oidc-client-secret" = module.argo-workflow-openid-client.config.client_secret
  }
}

module "argo-workflow-openid-client" {
  source = "../keycloak-client"

  realm_id = var.realm_id
  client_id = "argo-server-sso"
  external-url = var.external-url
  # role_mapping = {
  #   "admin" = ["argo_admin"]
  #   "developer" = ["argo_developer"]
  #   "analyst" = ["argo_viewer"]
  # }

  callback-url-paths = [
    "https://${var.external-url}/oauth2/callback"
  ]
}

resource "kubernetes_manifest" "argo-workflows-middleware-stripprefix" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "qhub-argo-workflows-stripprefix"
      namespace = var.namespace
    }
    spec = {
      stripPrefix = {
        prefixes = [
          "/${local.argo-workflows-prefix}/"
        ]
        forceSlash = false
      }
    }
  }
}

resource "kubernetes_manifest" "argo-workflows-ingress-route" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "argo-workflows"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && PathPrefix(`/${local.argo-workflows-prefix}`)"

          middlewares = concat(
            [{
              name      = kubernetes_manifest.argo-workflows-middleware-stripprefix.manifest.metadata.name
              namespace = var.namespace
            }]
          )

          services = [
            {
              name      = "${local.name}-server"
              port      = 2746
              namespace = var.namespace
            }
          ]
        }
      ]
    }
  }
}
