terraform {
  required_providers {
{%- if cookiecutter.provider == "aws" %}
    aws = {
      source = "hashicorp/aws"
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
    }
  }
  required_version = ">= 0.13"
}
