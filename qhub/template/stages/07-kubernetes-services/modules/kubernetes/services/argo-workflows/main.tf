# resource "kubernetes_service_account" "main" {
#   metadata {
#     name      = "jupyterflow-service-account"
#     namespace = var.namespace
#   }
# }


# resource "kubernetes_cluster_role" "main" {
#   metadata {
#     name = "argo-workflows-role"
#   }

#   rule {
#     api_groups = [""]
#     resources  = ["pods"]
#     verbs      = ["get", "list", "watch", "patch"]
#     # pod get/watch is used to identify the container IDs of the current pod
#     # pod patch is used to annotate the step's outputs back to controller (e.g. artifact location)
#   }

#   rule {
#     api_groups = [""]
#     resources  = ["pods/log"]
#     verbs      = ["get", "watch"]
#     # logs get/watch are used to get the pods logs for script outputs, and for log archival
#   }

#   rule {
#     api_groups = ["argoproj.io"]
#     resources  = ["workflows"]
#     verbs      = ["get", "list", "watch", "patch", "create"]
#   }

# }


# resource "kubernetes_role_binding" "main" {
#   metadata {
#     name = "jupyterflow-role-binding"
#     namespace = var.namespace
#   }

#   role_ref {
#     api_group = "rbac.authorization.k8s.io"
#     kind      = "Role"
#     name      = kubernetes_cluster_role.main.metadata.0.name
#   }
#   subject {
#     kind      = "ServiceAccount"
#     name      = kubernetes_service_account.main.metadata.0.name
#     namespace = var.namespace
#   }
# }

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
      # -- Restrict Argo to operate only in a single namespace (the namespace of the Helm release)
      singleNamespace = true
      workflowNamespaces = "${var.namespace}-argo"  # doesn't seem to be observed yet
      server = {
        # `sso` for OIDC/OAuth
        extraArgs = ["--auth-mode=sso", "--insecure-skip-verify"]
        # to enable TLS, set `secure = true`
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


      # -- Globally limits the rate at which pods are created.
      # controller = {
      #   parallelism = {
      #     resourceRateLimit = {
      #       limit = 10
      #       burst = 1
      #     }
      #   }
      # }

      # containerRuntimeExecutor = "emissary"

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
