terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.16.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.35.1"
    }
  }
  required_version = ">= 1.0"
}
