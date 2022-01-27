variable "kube_context" {
  description = "Optional kubernetes context to use to connect to kubernetes cluster"
  type        = string
}

output "kubernetes_credentials" {
  description = "Parameters needed to connect to kubernetes cluster locally"
  value       = {
    config_path = "~/.kube/config"
    config_context = var.kube_context
  }
}
