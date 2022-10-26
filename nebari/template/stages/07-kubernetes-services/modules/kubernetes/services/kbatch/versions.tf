terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "2.1.2"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.7.1"
    }
  }
  required_version = ">= 1.0"
}

locals {
  kbatch_service_account_name = "kbatch-kbatch-proxy"
  kbatch_version              = "0.4.1"
}
