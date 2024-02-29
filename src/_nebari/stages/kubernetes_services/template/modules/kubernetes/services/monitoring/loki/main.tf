resource "helm_release" "grafana-loki" {
  name       = "grafana-loki"
  namespace  = var.namespace
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki"
  version    = var.loki-helm-chart-version

  values = concat([
    file("${path.module}/values_loki.yaml"),
    jsonencode({
    })
  ], var.overrides)
}


resource "helm_release" "grafana-promtail" {
  name       = "grafana-promtail"
  namespace  = var.namespace
  repository = "https://grafana.github.io/helm-charts"
  chart      = "promtail"
  version    = var.promtail-helm-chart-version

  values = concat([
    file("${path.module}/values_promtail.yaml"),
    jsonencode({
    })
  ], var.overrides)
}
