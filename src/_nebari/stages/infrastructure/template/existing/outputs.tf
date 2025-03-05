output "kubernetes_credentials" {
  description = "Parameters needed to connect to kubernetes cluster locally"
  value = {
    config_path    = pathexpand("~/.kube/config")
    config_context = var.kube_context
  }
}

output "kubeconfig_filename" {
  description = "filename for nebari kubeconfig"
  value       = pathexpand("~/.kube/config")
}
