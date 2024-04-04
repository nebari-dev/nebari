resource "helm_release" "autoscaler" {
  name      = "cluster-autoscaler"
  namespace = var.namespace

  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  version    = "9.19.0"

  values = concat([
    jsonencode({
      rbac = {
        create = true
      }

      cloudProvider = "aws"
      awsRegion     = var.aws_region

      autoDiscovery = {
        clusterName = var.cluster-name
        enabled     = true
      }

      affinity = {
        nodeAffinity = {
          requiredDuringSchedulingIgnoredDuringExecution = {
            nodeSelectorTerms = [
              {
                matchExpressions = [
                  {
                    key      = "eks.amazonaws.com/nodegroup"
                    operator = "In"
                    values   = ["general"]
                  }
                ]
              }
            ]
          }
        }
      }
    })
  ], var.overrides)
}
