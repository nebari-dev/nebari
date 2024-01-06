terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "2.1.2"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.20.0"
    }
    required_providers {
      aws = {
        source  = "hashicorp/aws"
        version = "3.73.0"
      }
    }
  }
  required_version = ">= 1.0"
}
