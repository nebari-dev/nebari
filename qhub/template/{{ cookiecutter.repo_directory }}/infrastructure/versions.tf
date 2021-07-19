terraform {
  required_providers {
{%- if cookiecutter.provider == "aws" %}
    aws = {
      source = "hashicorp/aws"
    }
{%- elif cookiecutter.provider == "azure" %}
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=2.44.0"
    }
{%- elif cookiecutter.provider == "gcp" %}
    google = {
      source = "hashicorp/google"
    }
{%- elif cookiecutter.provider == "do" %}
    digitalocean = {
      source = "digitalocean/digitalocean"
    }
{% endif %}
    helm = {
      source  = "hashicorp/helm"
      version = "2.1.2"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.3.2"
    }
    kubernetes-alpha = {
      source  = "hashicorp/kubernetes-alpha"
      version = "0.3.2"
    }
  }
  required_version = ">= 0.13"
}
