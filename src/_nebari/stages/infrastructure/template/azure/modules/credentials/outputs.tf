output "credentials" {
  description = "Credentials required for connecting to Kubernetes cluster"
  sensitive   = true
  value = {
    endpoint               = var.azure_rbac_enabled ? var.kube_admin_config.host : var.kube_config.host
    username               = var.azure_rbac_enabled ? var.kube_admin_config.username : var.kube_config.username
    password               = var.azure_rbac_enabled ? var.kube_admin_config.password : var.kube_config.password
    client_certificate     = var.azure_rbac_enabled ? base64decode(var.kube_admin_config.client_certificate) : base64decode(var.kube_config.client_certificate)
    client_key             = var.azure_rbac_enabled ? base64decode(var.kube_admin_config.client_key) : base64decode(var.kube_config.client_key)
    cluster_ca_certificate = var.azure_rbac_enabled ? base64decode(var.kube_admin_config.cluster_ca_certificate) : base64decode(var.kube_config.cluster_ca_certificate)
  }
}
