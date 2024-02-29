resource "helm_release" "loki-grafana" {
  name       = "loki-grafana"
  namespace  = var.namespace
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki"
  version    = var.loki-helm-chart-version

  values = concat([
    file("${path.module}/values.yaml"),
    jsonencode({
    })
  ], var.overrides)
}
