terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "2.17.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.35.1"
    }
    keycloak = {
      source  = "mrparkers/keycloak"
      version = "3.7.0"
    }
  }
  required_version = ">= 1.0"
}
