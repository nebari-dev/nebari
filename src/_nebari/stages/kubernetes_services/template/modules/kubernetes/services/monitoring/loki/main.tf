resource "random_password" "minio_root_password" {
  length  = 32
  special = false
}


resource "helm_release" "loki-minio" {
  name       = "nebari-loki-minio"
  namespace  = var.namespace
  repository = "https://charts.min.io/"
  chart      = "minio"
  version    = var.minio-helm-chart-version

  values = concat([
    file("${path.module}/values_minio.yaml"),
    jsonencode({
      rootUser: "admin",
      rootPassword: random_password.minio_root_password.result,
    })
  ], var.grafana-loki-minio-overrides)
}


resource "helm_release" "grafana-loki" {
  name       = "nebari-loki"
  namespace  = var.namespace
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki"
  version    = var.loki-helm-chart-version

  values = concat([
    file("${path.module}/values_loki.yaml"),
    jsonencode({
      loki: {
        storage: {
          s3: {
            endpoint: "http://admin:${random_password.minio_root_password.result}@grafana-loki-minio:9000"
          }
        }
      }
      storageConfig: {
        # We configure MinIO by using the AWS config because MinIO implements the S3 API
        aws: {
          s3: "http://admin:${random_password.minio_root_password.result}@grafana-loki-minio:9000"
          s3forcepathstyle: true
        }
      }
    })
  ], var.grafana-loki-overrides)

  depends_on = [helm_release.loki-minio]
}

resource "helm_release" "grafana-promtail" {
  name       = "nebari-promtail"
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
