locals {
  # Prefix name for terraform state resources
  state_resource_name = "${var.name }-${var.namespace}-terraform-state"
}

resource "azurerm_resource_group" "terraform-resource-group" {
  name     = local.state_resource_name
  location = var.location
}

resource "azurerm_storage_account" "terraform-storage-account" {
  name                     = replace("${local.state_resource_name}${var.storage_account_postfix}", "-", "") # must be unique across the entire Azure service
  resource_group_name      = azurerm_resource_group.terraform-resource-group.name
  location                 = azurerm_resource_group.terraform-resource-group.location
  account_tier             = "Standard"
  account_replication_type = "GRS"

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_storage_container" "storage_container" {
  name                  = local.state_resource_name
  storage_account_name  = azurerm_storage_account.terraform-storage-account.name
  container_access_type = "private"
}
