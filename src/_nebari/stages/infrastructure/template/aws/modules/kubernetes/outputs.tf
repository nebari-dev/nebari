output "credentials" {
  description = "AWS eks credentials"
  sensitive   = true
  value = {
    endpoint = aws_eks_cluster.main.endpoint
    token    = data.aws_eks_cluster_auth.main.token
    cluster_ca_certificate = base64decode(
    aws_eks_cluster.main.certificate_authority.0.data)
  }
}

output "node_groups_arn" {
  value = aws_eks_node_group.main[*].arn
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster for the OpenID Connect identity provider"
  value       = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider"
  value       = aws_iam_openid_connect_provider.oidc_provider.arn
}

# https://github.com/terraform-aws-modules/terraform-aws-eks/blob/16f46db94b7158fd762d9133119206aaa7cf6d63/examples/self_managed_node_group/main.tf
output "kubeconfig" {
  description = "Kubernetes connection configuration kubeconfig"
  value = yamlencode({
    apiVersion      = "v1"
    kind            = "Config"
    current-context = "terraform"
    clusters = [{
      name = aws_eks_cluster.main.name
      cluster = {
        certificate-authority-data = aws_eks_cluster.main.certificate_authority[0].data
        server                     = aws_eks_cluster.main.endpoint
      }
    }]
    contexts = [{
      name = "terraform"
      context = {
        cluster = aws_eks_cluster.main.name
        user    = "terraform"
      }
    }]
    users = [{
      name = "terraform"
      user = {
        token = data.aws_eks_cluster_auth.main.token
      }
    }]
  })
}
