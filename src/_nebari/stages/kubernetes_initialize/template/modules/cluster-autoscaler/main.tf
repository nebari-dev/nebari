resource "helm_release" "autoscaler" {
  name      = "cluster-autoscaler"
  namespace = var.namespace

  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  version    = "9.52.1"

  values = concat([
    jsonencode({
      rbac = {
        create = true
        serviceAccount = {
          name = "cluster-autoscaler"
          # Pod Identity doesn't require annotations - association is handled via EKS Pod Identity
        }
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
