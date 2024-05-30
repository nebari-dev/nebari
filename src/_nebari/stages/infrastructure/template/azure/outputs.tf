output "kubernetes_credentials" {
  description = "Parameters needed to connect to kubernetes cluster"
  sensitive   = true
  value = {
    username               = module.kubernetes.credentials.username
    password               = module.kubernetes.credentials.password
    client_certificate     = module.kubernetes.credentials.client_certificate
    client_key             = module.kubernetes.credentials.client_key
    cluster_ca_certificate = module.kubernetes.credentials.cluster_ca_certificate
    host                   = module.kubernetes.credentials.endpoint
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

output "cluster_oidc_issuer_url" {
  description = "The OpenID Connect issuer URL that is associated with the AKS cluster"
  value       = module.kubernetes.cluster_oidc_issuer_url
}

output "resource_group_name" {
  description = "The name of the resource group in which the AKS cluster is created"
  value       = module.kubernetes.resource_group_name
}
