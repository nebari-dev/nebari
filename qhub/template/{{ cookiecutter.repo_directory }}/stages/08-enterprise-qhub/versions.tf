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
    keycloak = {
      source  = "mrparkers/keycloak"
      version = "3.3.0"
    }
  }
  required_version = ">= 1.0"
}
