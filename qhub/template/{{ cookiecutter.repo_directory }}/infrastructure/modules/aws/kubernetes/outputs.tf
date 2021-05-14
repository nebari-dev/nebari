output "credentials" {
  description = "AWS eks credentials"
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
