resource "helm_release" "prometheus-grafana" {
  name       = "nebari"
  namespace  = var.namespace
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "30.1.0"

  values = concat([
    file("${path.module}/values.yaml"),
    # https://github.com/prometheus-community/helm-charts/blob/kube-prometheus-stack-30.1.0/charts/kube-prometheus-stack/values.yaml
    jsonencode({
    })
  ], var.overrides)
}


module "grafana-client-id" {
  source = "../keycloak-client"

  realm_id     = var.realm_id
  client_id    = "grafana"
  external-url = var.external-url
  role_mapping = {
    "admin"     = ["grafana_admin"]
    "developer" = ["grafana_developer"]
    "analyst"   = ["grafana_viewer"]
  }
  callback-url-paths = [
    "https://${var.external-url}/monitoring/login/generic_oauth"
  ]
}


resource "kubernetes_config_map" "dashboard" {
  for_each = var.dashboards
  metadata {
    name      = "nebari-grafana-dashboards-${lower(each.value)}"
    namespace = var.namespace
    labels = {
      # grafana_dashboard label needed for grafana to pick it up
      # automatically
      grafana_dashboard = "1"
    }
    annotations = {
      "dashboard/subdirectory" = "${each.value}"
    }
  }

  data = {
    for dashboard_file in fileset("${path.module}/dashboards/${each.value}", "*.json") :
    dashboard_file => file("${path.module}/dashboards/${each.value}/${dashboard_file}")
  }
}


resource "kubernetes_manifest" "grafana-ingress-route" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "grafana-ingress-route"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && PathPrefix(`/monitoring`)"
          services = [
            {
              name      = "nebari-grafana"
              port      = 80
              namespace = var.namespace
            }
          ]
        }
      ]
    }
  }
}
