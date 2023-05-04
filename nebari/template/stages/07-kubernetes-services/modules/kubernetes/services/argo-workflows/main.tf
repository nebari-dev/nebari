locals {
  name                  = "argo-workflows"
  argo-workflows-prefix = "argo"
}

resource "helm_release" "argo-workflows" {
  name       = local.name
  namespace  = var.namespace
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-workflows"
  version    = "0.22.9"

  values = concat([
    file("${path.module}/values.yaml"),

    jsonencode({
      singleNamespace = true # Restrict Argo to operate only in a single namespace (the namespace of the Helm release)

      controller = {
        metricsConfig = {
          enabled = true # enable prometheus
        }
        workflowNamespaces = [
          "${var.namespace}"
        ]
        nodeSelector = {
          "${var.node-group.key}" = var.node-group.value
        }
      }

      server = {
        # `sso` for OIDC/OAuth
        extraArgs = ["--auth-mode=sso", "--insecure-skip-verify"]
        # to enable TLS, `secure = true`
        secure   = false
        baseHref = "/${local.argo-workflows-prefix}/"

        sso = {
          insecureSkipVerify = true
          issuer             = "https://${var.external-url}/auth/realms/${var.realm_id}"
          clientId = {
            name = "argo-server-sso"
            key  = "argo-oidc-client-id"
          }
          clientSecret = {
            name = "argo-server-sso"
            key  = "argo-oidc-client-secret"
          }
          # The OIDC redirect URL. Should be in the form <argo-root-url>/oauth2/callback.
          redirectUrl = "https://${var.external-url}/${local.argo-workflows-prefix}/oauth2/callback"
          rbac = {
            # https://argoproj.github.io/argo-workflows/argo-server-sso/#sso-rbac
            enabled         = true
            secretWhitelist = []
          }
          customGroupClaimName = "roles"
          scopes               = ["roles"]
        }
        nodeSelector = {
          "${var.node-group.key}" = var.node-group.value
        }
      }

    })
  ], var.overrides)
}

resource "kubernetes_secret" "argo-oidc-secret" {
  metadata {
    name      = "argo-server-sso"
    namespace = var.namespace
  }
  data = {
    "argo-oidc-client-id"     = module.argo-workflow-openid-client.config.client_id
    "argo-oidc-client-secret" = module.argo-workflow-openid-client.config.client_secret
  }
}

module "argo-workflow-openid-client" {
  source = "../keycloak-client"

  realm_id     = var.realm_id
  client_id    = "argo-server-sso"
  external-url = var.external-url
  role_mapping = {
    "admin"     = ["argo_admin"]
    "developer" = ["argo_developer"]
    "analyst"   = ["argo_viewer"]
  }

  callback-url-paths = [
    "https://${var.external-url}/${local.argo-workflows-prefix}/oauth2/callback"
  ]
}

resource "kubernetes_manifest" "argo-workflows-middleware-stripprefix" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "nebari-argo-workflows-stripprefix"
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

resource "kubernetes_service_account_v1" "argo-admin-sa" {
  metadata {
    name      = "argo-admin"
    namespace = var.namespace
    annotations = {
      "workflows.argoproj.io/rbac-rule" : "'argo_admin' in groups"
      "workflows.argoproj.io/rbac-rule-precedence" : "11"
    }
  }
}

resource "kubernetes_secret_v1" "argo_admin_sa_token" {
  metadata {
    name      = "argo-admin.service-account-token"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/service-account.name" = kubernetes_service_account_v1.argo-admin-sa.metadata[0].name

    }
  }
  type = "kubernetes.io/service-account-token"
}

resource "kubernetes_cluster_role_binding" "argo-admin-rb" {
  metadata {
    name = "argo-admin"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "argo-workflows-admin" # role deployed as part of helm chart
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.argo-admin-sa.metadata.0.name
    namespace = var.namespace
  }
}

resource "kubernetes_service_account_v1" "argo-dev-sa" {
  metadata {
    name      = "argo-dev"
    namespace = var.namespace
    annotations = {
      "workflows.argoproj.io/rbac-rule" : "'argo_developer' in groups"
      "workflows.argoproj.io/rbac-rule-precedence" : "10"
    }
  }
}

resource "kubernetes_secret_v1" "argo_dev_sa_token" {
  metadata {
    name      = "argo-dev.service-account-token"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/service-account.name" = kubernetes_service_account_v1.argo-dev-sa.metadata[0].name
    }
  }
  type = "kubernetes.io/service-account-token"
}

resource "kubernetes_cluster_role_binding" "argo-dev-rb" {
  metadata {
    name = "argo-dev"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "argo-workflows-edit" # role deployed as part of helm chart
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.argo-dev-sa.metadata.0.name
    namespace = var.namespace
  }
}


resource "kubernetes_service_account_v1" "argo-view-sa" {
  metadata {
    name      = "argo-viewer"
    namespace = var.namespace
    annotations = {
      "workflows.argoproj.io/rbac-rule" : "'argo_viewer' in groups"
      "workflows.argoproj.io/rbac-rule-precedence" : "9"
    }
  }
}

resource "kubernetes_secret_v1" "argo_viewer_sa_token" {
  metadata {
    name      = "argo-viewer.service-account-token"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/service-account.name" = kubernetes_service_account_v1.argo-view-sa.metadata[0].name
    }
  }
  type = "kubernetes.io/service-account-token"
}

resource "kubernetes_cluster_role_binding" "argo-view-rb" {
  metadata {
    name = "argo-view"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "argo-workflows-view" # role deployed as part of helm chart
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.argo-view-sa.metadata.0.name
    namespace = var.namespace
  }
}
