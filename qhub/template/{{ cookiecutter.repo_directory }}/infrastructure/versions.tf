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
{%- elif cookiecutter.provider == "kind" %}
    kind = {
      source = "kyma-incubator/kind"
      version = "0.0.7"
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
