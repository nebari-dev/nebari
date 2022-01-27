output "kubernetes_credentials" {
  description = "Parameters needed to connect to kubernetes cluster"
  value       = {
    username               = module.kubernetes.credentials.username
    password               = module.kubernetes.credentials.password
    client_certificate     = module.kubernetes.credentials.client_certificate
    client_key             = module.kubernetes.credentials.client_key
    cluster_ca_certificate = module.kubernetes.credentials.cluster_ca_certificate
    host                   = module.kubernetes.credentials.endpoint
  }
}
