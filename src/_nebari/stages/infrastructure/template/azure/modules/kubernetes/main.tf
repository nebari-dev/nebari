# https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/kubernetes_cluster
resource "azurerm_kubernetes_cluster" "main" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags

  # To enable Azure AD Workload Identity oidc_issuer_enabled must be set to true.
  oidc_issuer_enabled       = var.workload_identity_enabled
  workload_identity_enabled = var.workload_identity_enabled

  # DNS prefix specified when creating the managed cluster. Changing this forces a new resource to be created.
  dns_prefix = "Nebari" # required

  # Azure requires that a new, non-existent Resource Group is used, as otherwise the provisioning of the Kubernetes Service will fail.
  node_resource_group     = var.node_resource_group_name
  private_cluster_enabled = var.private_cluster_enabled

  dynamic "network_profile" {
    for_each = var.network_profile != null ? [var.network_profile] : []
    content {
      network_plugin     = network_profile.value.network_plugin != null ? network_profile.value.network_plugin : null
      network_policy     = network_profile.value.network_policy != null ? network_profile.value.network_policy : null
      service_cidr       = network_profile.value.service_cidr != null ? network_profile.value.service_cidr : null
      dns_service_ip     = network_profile.value.dns_service_ip != null ? network_profile.value.dns_service_ip : null
      docker_bridge_cidr = network_profile.value.docker_bridge_cidr != null ? network_profile.value.docker_bridge_cidr : null
    }
  }

  kubernetes_version = var.kubernetes_version
  default_node_pool {
    vnet_subnet_id      = var.vnet_subnet_id
    name                = var.node_groups[0].name
    vm_size             = var.node_groups[0].instance_type
    enable_auto_scaling = "true"
    min_count           = var.node_groups[0].min_size
    max_count           = var.node_groups[0].max_size
    max_pods            = var.max_pods

    orchestrator_version = var.kubernetes_version
    node_labels = {
      "azure-node-pool" = var.node_groups[0].name
    }
    tags = var.tags

    # temparory_name_for_rotation must be <= 12 characters
    temporary_name_for_rotation = "${substr(var.node_groups[0].name, 0, 9)}tmp"
  }

  sku_tier = "Free" # "Free" [Default] or "Paid"

  identity {
    type = "SystemAssigned" # "UserAssigned" or "SystemAssigned".  SystemAssigned identity lifecycles are tied to the AKS Cluster.
  }

  lifecycle {
    ignore_changes = [
      # We ignore changes since otherwise, the AKS cluster unsets this default value every time you deploy.
      # https://github.com/hashicorp/terraform-provider-azurerm/issues/24020#issuecomment-1887670287
      default_node_pool[0].upgrade_settings,
    ]
  }

}

# https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/kubernetes_cluster_node_pool
resource "azurerm_kubernetes_cluster_node_pool" "node_group" {
  for_each = { for i, group in var.node_groups : i => group if i != 0 }

  name                  = each.value.name
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = each.value.instance_type
  enable_auto_scaling   = "true"
  mode                  = "User" # "System" or "User", only "User" nodes can scale down to 0
  min_count             = each.value.min_size
  max_count             = each.value.max_size
  max_pods              = var.max_pods
  node_labels = {
    "azure-node-pool" = each.value.name
  }
  orchestrator_version = var.kubernetes_version
  tags                 = var.tags
  vnet_subnet_id       = var.vnet_subnet_id
}
