resource "helm_release" "postgresql" {
  name      = "postgresql"
  namespace = var.namespace

  repository = "https://charts.bitnami.com/bitnami"
  chart      = "bitnami/postgresql"
  version    = "10.13.12"

  values = concat([
    file("${path.module}/values.yaml"),
  ], var.overrides)
}
