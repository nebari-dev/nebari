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

module "terraform-state" {
  source = "./modules/terraform-state"

  name     = "${var.name}-${var.namespace}"
  location = var.region
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.83.0"
    }
  }
  required_version = ">= 1.0"
}
