resource "helm_release" "loki-grafana" {
  name       = "nebari"
  namespace  = var.namespace
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana/loki"
  version    = var.loki-helm-chart-version

  values = file("${path.module}/values.yaml")
}

resource "kubernetes_manifest" "grafana-ingress-route" {
  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "IngressRoute"
    metadata = {
      name      = "grafana-loki-ingress-route"
      namespace = var.namespace
    }
    spec = {
      entryPoints = ["websecure"]
      routes = [
        {
          kind  = "Rule"
          match = "Host(`${var.external-url}`) && PathPrefix(`/loki`)"
          services = [
            {
              name      = "nebari-grafana-loki"
              port      = 80
              namespace = var.namespace
            }
          ]
        }
      ]
    }
  }
}
