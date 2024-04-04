variable "name" {
  description = "Prefix name to assign to Nebari resources"
  type        = string
}

variable "namespace" {
  description = "Namespace to create Kubernetes resources"
  type        = string
}

variable "region" {
  description = "Region for AWS deployment"
  type        = string
}

variable "storage_account_postfix" {
  description = "Prefix to assign to storage account to ensure it is unique"
  type        = string
}

variable "state_resource_group_name" {
  description = "Name for terraform state resource group"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

provider "azurerm" {
  features {}
}

module "terraform-state" {
  source = "./modules/terraform-state"

  name                    = "${var.name}-${var.namespace}"
  resource_group_name     = var.state_resource_group_name
  location                = var.region
  storage_account_postfix = var.storage_account_postfix
  tags                    = var.tags
}

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.97.1"
    }
  }
  required_version = ">= 1.0"
}
