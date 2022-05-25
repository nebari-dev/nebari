variable "name" {
  description = "Prefix name to assign to QHub resources"
  type        = string
}

variable "namespace" {
  description = "Namespace to create Kubernetes resources"
  type        = string
}

variable "region" {
  description = "Region for Digital Ocean deployment"
  type        = string
}

provider "digitalocean" {

}

module "terraform-state" {
  source = "./modules/terraform-state"

  name   = "${var.name}-${var.namespace}"
  region = var.region
}

terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "2.17.0"
    }
  }
  required_version = ">= 1.0"
}
