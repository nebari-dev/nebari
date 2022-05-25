# https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/kubernetes_cluster
resource "azurerm_kubernetes_cluster" "main" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name

  # DNS prefix specified when creating the managed cluster. Changing this forces a new resource to be created.
  dns_prefix = "Qhub" # required

  # Azure requires that a new, non-existent Resource Group is used, as otherwise the provisioning of the Kubernetes Service will fail.
  node_resource_group     = var.node_resource_group_name
  private_cluster_enabled = var.private_cluster_enabled

  kubernetes_version = var.kubernetes_version
  default_node_pool {
    vnet_subnet_id      = var.vnet_subnet_id
    name                = var.node_groups[0].name
    node_count          = 1
    vm_size             = var.node_groups[0].instance_type
    enable_auto_scaling = "true"
    min_count           = 1
    max_count           = 1
    # node_labels          = var.node_labels
    orchestrator_version = var.kubernetes_version
    node_labels = {
      "azure-node-pool" = var.node_groups[0].name
    }
  }

  sku_tier = "Free" # "Free" [Default] or "Paid"

  identity {
    type = "SystemAssigned" # "UserAssigned" or "SystemAssigned".  SystemAssigned identity lifecycles are tied to the AKS Cluster.
  }

  # tags = var.tags
}

# https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/kubernetes_cluster_node_pool
resource "azurerm_kubernetes_cluster_node_pool" "user_node_group" {
  name                  = var.node_groups[1].name
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = var.node_groups[1].instance_type
  node_count            = 0
  enable_auto_scaling   = "true"
  mode                  = "User" # "System" or "User", only "User" nodes can scale down to 0
  min_count             = var.node_groups[1].min_size
  max_count             = var.node_groups[1].max_size
  node_labels = {
    "azure-node-pool" = var.node_groups[1].name
  }
  orchestrator_version = var.kubernetes_version
}

resource "azurerm_kubernetes_cluster_node_pool" "worker_node_group" {
  name                  = var.node_groups[2].name
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = var.node_groups[2].instance_type
  node_count            = 0
  enable_auto_scaling   = "true"
  mode                  = "User" # "System" or "User", only "User" nodes can scale down to 0
  min_count             = var.node_groups[2].min_size
  max_count             = var.node_groups[2].max_size
  node_labels = {
    "azure-node-pool" = var.node_groups[2].name
  }
  orchestrator_version = var.kubernetes_version
}
