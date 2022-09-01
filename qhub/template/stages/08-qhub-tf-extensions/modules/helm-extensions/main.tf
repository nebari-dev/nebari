resource "helm_release" "custom-helm-deployment" {
  name       = var.name
  namespace  = var.namespace
  repository = var.repository
  chart      = var.chart
  version    = var.chart_version

  values = [jsonencode(var.overrides)]
}
