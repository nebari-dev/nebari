output "kubernetes_credentials" {
  description = "Parameters needed to connect to kubernetes cluster"
  value       = {
    host                   = module.kubernetes.credentials.endpoint
    cluster_ca_certificate = module.kubernetes.credentials.cluster_ca_certificate
    token                  = module.kubernetes.credentials.token
  }
}
