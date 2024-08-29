resource "azurerm_resource_group" "terraform-state-resource-group" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

resource "azurerm_storage_account" "terraform-state-storage-account" {
  # name, can only consist of lowercase letters and numbers, and must be between 3 and 24 characters long
  name                     = replace("${var.name}${var.storage_account_postfix}", "-", "") # must be unique across the entire Azure service
  resource_group_name      = azurerm_resource_group.terraform-state-resource-group.name
  location                 = azurerm_resource_group.terraform-state-resource-group.location
  account_tier             = "Standard"
  account_replication_type = "GRS"
  tags                     = var.tags
  min_tls_version          = "TLS1_2"

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_storage_container" "storage_container" {
  name                  = "${var.name}-state"
  storage_account_name  = azurerm_storage_account.terraform-state-storage-account.name
  container_access_type = "private"
}
