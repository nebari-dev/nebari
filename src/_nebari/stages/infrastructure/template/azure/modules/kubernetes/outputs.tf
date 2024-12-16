output "credentials" {
  description = "Credentials required for connecting to Kubernetes cluster"
  sensitive   = true
  value = {
    endpoint               = var.azure_rbac.enable ? azurerm_kubernetes_cluster.main.kube_admin_config.0.host : azurerm_kubernetes_cluster.main.kube_config.0.host
    username               = var.azure_rbac.enable ? azurerm_kubernetes_cluster.main.kube_admin_config.0.username : azurerm_kubernetes_cluster.main.kube_config.0.username
    password               = var.azure_rbac.enable ? azurerm_kubernetes_cluster.main.kube_admin_config.0.password : azurerm_kubernetes_cluster.main.kube_config.0.password
    client_certificate     = var.azure_rbac.enable ? azurerm_kubernetes_cluster.main.kube_admin_config.0.client_certificate : azurerm_kubernetes_cluster.main.kube_config.0.client_certificate
    client_key             = var.azure_rbac.enable ? azurerm_kubernetes_cluster.main.kube_admin_config.0.client_key : azurerm_kubernetes_cluster.main.kube_config.0.client_key
    cluster_ca_certificate = var.azure_rbac.enable ? azurerm_kubernetes_cluster.main.kube_admin_config.0.cluster_ca_certificate : azurerm_kubernetes_cluster.main.kube_config.0.cluster_ca_certificate
  }
}

output "kubeconfig" {
  description = "Kubernetes connection kubeconfig"
  sensitive   = true
  value       = var.azure_rbac.enable ? azurerm_kubernetes_cluster.main.kube_admin_config_raw : azurerm_kubernetes_cluster.main.kube_config_raw
}

output "cluster_oidc_issuer_url" {
  description = "The OpenID Connect issuer URL that is associated with the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.oidc_issuer_url
}

output "resource_group_name" {
  description = "The name of the resource group in which the AKS cluster is created"
  value       = azurerm_kubernetes_cluster.main.resource_group_name
}
