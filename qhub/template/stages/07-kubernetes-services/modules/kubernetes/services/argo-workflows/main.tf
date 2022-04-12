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
# resource "kubernetes_namespace" "main" {
#   metadata {
#     # labels = merge({}, var.labels)

#     name = var.argo-workflows-namespace
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
      singleNamespace = true  # Restrict Argo to operate only in a single namespace (the namespace of the Helm release)

      # workflow = {
      #   serviceAccount = {
      #     create = true  # turning off permissions
      #     name = "argo-workflow-service-account"  # default is "argo-workflow"
      #   }
      #   rbac = {
      #     create = true  # turning off permissions
      #   }
      # }
      controller = {
      #   serviceAccount = {
      #     create = true  # turning off permissions
      #     name = "argo-controller-service-account"
      #   }
      #   rbac = {
      #     create = true  # turning off permissions
      #   }
        podAnnotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/path"   = "/metrics"
          "prometheus.io/port"   = "9090"
        }
        metricsConfig = {
          enabled = true  # enable prometheus
        }
        workflowNamespaces = [
          "${var.namespace}"
          ]
      #   # containerRuntimeExecutor = "emissary"
      #   logging = {
      #     level = "debug"
      #   }
      }

      server = {
        enabled = true

        # serviceAccount = {
        #   create = false  # turning off permissions (argo server won't start without this)
        #   name = "argo-workflows-server-service-account"
        # }
        # rbac = {
        #   create = false # turning off permissions (argo server won't start without this)
        # }
      #   // this auth mode is for dev mode only
        extraArgs = ["--auth-mode=server"]
        baseHref = "/${local.argo-workflows-prefix}/"
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
