resource "azurerm_resource_group" "terraform-state-resource-group" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# DELETEME: This is where we create the storage account
resource "azurerm_storage_account" "terraform-state-storage-account" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.terraform-state-resource-group.name
  location                 = azurerm_resource_group.terraform-state-resource-group.location
  account_tier             = "Standard"
  account_replication_type = "GRS"
  tags                     = var.tags

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_storage_container" "storage_container" {
  name                  = var.storage_container_name
  storage_account_name  = azurerm_storage_account.terraform-state-storage-account.name
  container_access_type = "private"
}
