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


resource "helm_release" "argo-workflows" {
  name       = "qhub-argo-workflows"
  namespace  = var.namespace
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-workflows"
  version    = "0.13.1"

  values = concat([
    file("${path.module}/values.yaml"),
    # https://github.com/argoproj/argo-helm/blob/argo-workflows-0.13.1/charts/argo-workflows/values.yaml


    jsonencode({
      # -- Restrict Argo to operate only in a single namespace (the namespace of the Helm release)
      # singleNamespace = true

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

      // this auth mode is for dev mode only
      server = {
        extraArgs = ["--auth-mode=server"]
      }

    })
  ], var.overrides)
}

# resource "kubernetes_manifest" "grafana-ingress-route" {
#   manifest = {
#     apiVersion = "traefik.containo.us/v1alpha1"
#     kind       = "IngressRoute"
#     metadata = {
#       name      = "grafana-ingress-route"
#       namespace = var.namespace
#     }
#     spec = {
#       entryPoints = ["websecure"]
#       routes = [
#         {
#           kind  = "Rule"
#           match = "Host(`${var.external-url}`) && PathPrefix(`/monitoring`)"
#           services = [
#             {
#               name      = "qhub-grafana"
#               port      = 80
#               namespace = var.namespace
#             }
#           ]
#         }
#       ]
#     }
#   }
# }
