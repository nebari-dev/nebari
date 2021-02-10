terraform {
  required_providers {
{%- if cookiecutter.provider == "aws" %}
    aws = {
      source = "hashicorp/aws"
{%- elif cookiecutter.provider == "azure" %}
    azure = {
      source = "hashicorp/azurerm"
      version = "=2.44.0"
{%- elif cookiecutter.provider == "gcp" %}
    google = {
      source = "hashicorp/google"
{%- elif cookiecutter.provider == "do" %}
    digitalocean = {
      source = "digitalocean/digitalocean"
{% endif %}
    }
    helm = {
      source = "hashicorp/helm"
    }
    kubernetes = {
      source = "hashicorp/kubernetes"
      version = "< 2"
    }
  }
  required_version = ">= 0.13"
}
