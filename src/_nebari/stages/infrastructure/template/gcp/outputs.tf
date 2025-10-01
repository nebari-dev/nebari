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

output "cluster_oidc_issuer_url" {
  description = "The OpenID Connect issuer URL that is associated with the GKE cluster"
  value       = module.kubernetes.cluster_oidc_issuer_url
}

output "project_id" {
  description = "The GCP project ID"
  value       = var.project_id
}
