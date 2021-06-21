resource "helm_release" "autoscaler" {
  name      = "cluster-autoscaler"
  namespace = var.namespace

  repository = "https://charts.helm.sh/stable"
  chart      = "cluster-autoscaler"
  version    = "7.1.0"

  values = concat([
    jsonencode({
      rbac = {
        create = true
      }

      cloudProvider = "aws"
      awsRegion     = var.aws-region

      autoDiscovery = {
        clusterName = var.cluster-name
        enabled     = true
      }
    })
  ], var.overrides)
}
