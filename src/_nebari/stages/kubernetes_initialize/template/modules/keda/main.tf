resource "helm_release" "keda" {
  name          = "keda"
  namespace     = var.namespace
  repository    = "https://kedacore.github.io/charts"
  chart         = "keda"
  version       = "2.13.2"
  wait_for_jobs = "true"
}
