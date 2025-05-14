output "kubernetes_credentials" {
  description = "Parameters needed to connect to kubernetes cluster"
  sensitive   = true
  value = {
    host                   = module.kubernetes.credentials.endpoint
    cluster_ca_certificate = module.kubernetes.credentials.cluster_ca_certificate
    token                  = module.kubernetes.credentials.token
  }
}

resource "local_file" "kubeconfig" {
  count = var.kubeconfig_filename != null ? 1 : 0

  content  = module.kubernetes.kubeconfig
  filename = var.kubeconfig_filename
}

output "kubeconfig_filename" {
  description = "filename for nebari kubeconfig"
  value       = var.kubeconfig_filename
}

output "nfs_endpoint" {
  description = "Endpoint for nfs server"
  value       = length(module.efs) == 1 ? module.efs[0].credentials.dns_name : null
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster for the OpenID Connect identity provider"
  value       = module.kubernetes.cluster_oidc_issuer_url
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider"
  value       = module.kubernetes.oidc_provider_arn
}

output "efs_id" {
  description = "EFS ID"
  value       = module.efs[0].efs_id
}

output "efs_storage_class_name" {
  description = "EFS storage class name"
  value       = module.storage-class.efs_storage_class_name
}

output "efs_storage_class_retain_name" {
  description = "EFS storage class name"
  value       = module.storage-class.efs_storage_class_retain_name
}
