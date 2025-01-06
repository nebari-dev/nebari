module "k8s_credentials" {
  source             = "../credentials"
  azure_rbac_enabled = var.azure_rbac.azure_rbac_enabled
  kube_admin_config  = azurerm_kubernetes_cluster.main.kube_admin_config[0]
  kube_config        = azurerm_kubernetes_cluster.main.kube_config[0]
}

output "credentials" {
  description = "Credentials required for connecting to Kubernetes cluster"
  sensitive   = true
  value       = module.k8s_credentials.credentials
}

output "kubeconfig" {
  description = "Kubernetes connection kubeconfig"
  sensitive   = true
  value       = var.azure_rbac.azure_rbac_enabled ? azurerm_kubernetes_cluster.main.kube_admin_config_raw : azurerm_kubernetes_cluster.main.kube_config_raw
}

output "cluster_oidc_issuer_url" {
  description = "The OpenID Connect issuer URL that is associated with the AKS cluster"
  value       = azurerm_kubernetes_cluster.main.oidc_issuer_url
}

output "resource_group_name" {
  description = "The name of the resource group in which the AKS cluster is created"
  value       = azurerm_kubernetes_cluster.main.resource_group_name
}
