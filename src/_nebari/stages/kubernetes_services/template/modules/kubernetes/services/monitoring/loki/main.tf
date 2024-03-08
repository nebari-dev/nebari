resource "random_password" "minio_root_password" {
  length  = 32
  special = false
}

locals {
  minio-url = "http://${var.minio-release-name}:${var.minio-port}"
  node-selector = {
    "${var.node-group.key}" = "${var.node-group.value}"
  }
}

resource "helm_release" "loki-minio" {
  count      = var.minio-enabled ? 1 : 0
  name       = var.minio-release-name
  namespace  = var.namespace
  repository = "https://raw.githubusercontent.com/bitnami/charts/defb094c658024e4aa8245622dab202874880cbc/bitnami"
  chart      = "minio"
  # last release that was Apache-2.0
  version = var.minio-helm-chart-version

  set {
    name  = "accessKey.password"
    value = "admin"
  }

  set {
    name  = "secretKey.password"
    value = random_password.minio_root_password.result
  }

  set {
    name  = "defaultBuckets"
    value = join(" ", var.buckets)
  }

  set {
    name  = "persistence.size"
    value = var.minio-storage
  }

  values = concat([
    file("${path.module}/values_minio.yaml"),
    jsonencode({
      nodeSelector : local.node-selector
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
      loki : {
        storage : {
          s3 : {
            endpoint : local.minio-url,
            accessKeyId : "admin"
            secretAccessKey : random_password.minio_root_password.result,
            s3ForcePathStyle : true
          }
        }
      }
      storageConfig : {
        # We configure MinIO by using the AWS config because MinIO implements the S3 API
        aws : {
          s3 : local.minio-url
          s3ForcePathStyle : true
        }
      }
      write : { nodeSelector : local.node-selector }
      read : { nodeSelector : local.node-selector }
      backend : { nodeSelector : local.node-selector }
      gateway : { nodeSelector : local.node-selector }
    })
  ], var.grafana-loki-overrides)

  depends_on = [helm_release.loki-minio]
}

resource "helm_release" "grafana-promtail" {
  # Promtail ships the contents of logs to Loki instance
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
