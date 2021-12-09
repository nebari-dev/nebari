resource "helm_release" "minio" {
  name      = "minio"
  namespace = var.namespace

  repository = "https://charts.bitnami.com/bitnami"
  chart      = "bitnami/minio"
  version    = "9.2.4"

  values = concat([
    file("${path.module}/values.yaml"),
  ], var.overrides)
}
