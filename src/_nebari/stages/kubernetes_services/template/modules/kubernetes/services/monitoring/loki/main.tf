resource "helm_release" "loki-minio" {
  name       = "grafana-loki-minio"
  namespace  = var.namespace
  repository = "https://charts.min.io/"
  chart      = "minio"
  version    = var.minio-helm-chart-version

  values = concat([
    file("${path.module}/values_minio.yaml"),
    jsonencode({
    })
  ], var.grafana-loki-minio-overrides)
}


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
  ], var.grafana-loki-overrides)

  depends_on = [helm_release.loki-minio]
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
  ], var.grafana-promtail-overrides)

  depends_on = [helm_release.grafana-loki]
}
