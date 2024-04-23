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

variable "storage_account_name" {
  description = "Name for terraform state storage account, must be unique across Azure, 3-24 characters long and only include lowercase letters and numbers"
  type        = string
}

variable "storage_container_name" {
  description = "Name for terraform state storage container"
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

  name                   = "${var.name}-${var.namespace}"
  resource_group_name    = var.state_resource_group_name
  location               = var.region
  tags                   = var.tags
  storage_account_name   = var.storage_account_name
  storage_container_name = var.storage_container_name
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
