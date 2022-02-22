variable "name" {
  description = "Prefix name to assign to QHub resources"
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

provider "azurerm" {
  features {}
}

module "terraform-state" {
  source = "./modules/terraform-state"

  name                          = "${var.name }-${var.namespace}"
  location                      = var.region
  storage_account_postfix       = var.storage_account_postfix
}

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=2.44.0"
    }
  }
  required_version = ">= 1.0"
}
