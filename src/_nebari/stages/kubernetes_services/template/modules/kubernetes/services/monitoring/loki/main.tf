resource "random_password" "minio_root_password" {
  length  = 32
  special = false
}

locals {
  minio-url = "http://admin:${random_password.minio_root_password.result}@${var.minio-release-name}:${var.minio-port}"
}

resource "helm_release" "loki-minio" {
  name       = var.minio-release-name
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
            endpoint: local.minio-url
          }
        }
      }
      storageConfig: {
        # We configure MinIO by using the AWS config because MinIO implements the S3 API
        aws: {
          s3: local.minio-url
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
