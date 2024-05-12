resource "helm_release" "keda" {
  name          = "keda"
  namespace     = var.namespace
  repository    = "https://kedacore.github.io/charts"
  chart         = "keda"
  version       = "2.13.2"
  wait_for_jobs = "true"
  values = concat([
    file("${path.module}/values.yaml"),
    jsonencode({
      nodeSelector = {
        "${var.general_node_selector.key}" = var.general_node_selector.value
      }
    })
  ])
}
