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
  description = "filename for qhub kubeconfig"
  value       = var.kubeconfig_filename
}

output "nfs_endpoint" {
  description = "Endpoint for nfs server"
  value       = module.efs.credentials.dns_name
}
