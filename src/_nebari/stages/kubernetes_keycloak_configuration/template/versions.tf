terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "2.1.2"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.35.1"
    }
    keycloak = {
      source = "keycloak/keycloak"
      version = "5.5.0"
    }
  }
  required_version = ">= 1.0"
}
