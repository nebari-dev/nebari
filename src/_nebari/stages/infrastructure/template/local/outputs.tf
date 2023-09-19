output "kubernetes_credentials" {
  description = "Parameters needed to connect to kubernetes cluster locally"
  sensitive   = true
  value = {
    config_path            = var.kubeconfig_filename
    host                   = kind_cluster.default.endpoint
    cluster_ca_certificate = kind_cluster.default.cluster_ca_certificate
    client_key             = kind_cluster.default.client_key
    client_certificate     = kind_cluster.default.client_certificate
  }
}

resource "local_file" "default" {
  content  = kind_cluster.default.kubeconfig
  filename = var.kubeconfig_filename
}

output "kubeconfig_filename" {
  description = "filename for nebari kubeconfig"
  value       = var.kubeconfig_filename
}
