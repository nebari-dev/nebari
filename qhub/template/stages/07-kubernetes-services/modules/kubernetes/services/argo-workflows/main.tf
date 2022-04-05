resource "kubernetes_service_account" "main" {
  metadata {
    name      = "jupyterflow-service-account"
    namespace = var.namespace
  }
}


resource "kubernetes_cluster_role" "main" {
  metadata {
    name = "argo-workflows-role"
  }

  rule {
    api_groups = [""]
    resources  = ["pods"]
    verbs      = ["get", "list", "watch", "patch"]
    # pod get/watch is used to identify the container IDs of the current pod
    # pod patch is used to annotate the step's outputs back to controller (e.g. artifact location)
  }

  rule {
    api_groups = [""]
    resources  = ["pods/log"]
    verbs      = ["get", "watch"]
    # logs get/watch are used to get the pods logs for script outputs, and for log archival
  }

  rule {
    api_groups = ["argoproj.io"]
    resources  = ["workflows"]
    verbs      = ["get", "list", "watch", "patch", "create"]
  }

}


resource "kubernetes_role_binding" "main" {
  metadata {
    name = "jupyterflow-role-binding"
    namespace = var.namespace
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_cluster_role.main.metadata.0.name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.main.metadata.0.name
    namespace = var.namespace
  }
}


resource "helm_release" "argo-workflows" {
  name       = "qhub-argo-workflows"
  namespace  = var.namespace
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-workflows"
  version    = "0.13.1"

#   values = concat([
#     file("${path.module}/values.yaml"),
#     # https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/values.yaml
#     jsonencode({
#       alertmanager = {
#         alertmanagerSpec = {
#           nodeSelector: {
#             "${var.node-group.key}" = var.node-group.value
#           }
#         }
#       }

#       prometheusOperator = {
#         nodeSelector = {
#           "${var.node-group.key}" = var.node-group.value
#         }

#         admissionWebhooks = {
#           patch = {
#             nodeSelector = {
#               "${var.node-group.key}" = var.node-group.value
#             }
#           }
#         }
#       }

#       kube-state-metrics = {
#         nodeSelector = {
#           "${var.node-group.key}" = var.node-group.value
#         }
#       }

#       prometheus = {
#         prometheusSpec = {
#           nodeSelector = {
#             "${var.node-group.key}" = var.node-group.value
#           }
#         }
#       }

#       # https://github.com/grafana/helm-charts/blob/main/charts/grafana/values.yaml
#       grafana = {
#         nodeSelector = {
#           "${var.node-group.key}" = var.node-group.value
#         }

#         "grafana.ini": {
#           server = {
#             protocol = "http"
#             domain = var.external-url
#             root_url = "https://%(domain)s/monitoring"
#             serve_from_sub_path = "true"
#           }

#           auth = {
#             oauth_auto_login = "true"
#           }

#           "auth.generic_oauth" = {
#             enabled = "true"
#             name = "Login Keycloak"
#             allow_sign_up = "true"
#             client_id = module.grafana-client-id.config.client_id
#             client_secret = module.grafana-client-id.config.client_secret
#             scopes = "profile"
#             auth_url = module.grafana-client-id.config.authentication_url
#             token_url = module.grafana-client-id.config.token_url
#             api_url = module.grafana-client-id.config.userinfo_url
#             tls_skip_verify_insecure = "true"
#             login_attribute_path = "preferred_username"
#             role_attribute_path = "contains(roles[*], 'grafana_admin') && 'Admin' || contains(roles[*], 'grafana_developer') && 'Editor' || contains(roles[*], 'grafana_viewer') || 'Viewer'"
#           }
#         }
#       }
#     })
#   ], var.overrides)
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
