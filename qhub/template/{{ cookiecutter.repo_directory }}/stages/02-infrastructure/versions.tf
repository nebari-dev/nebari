terraform {
  required_providers {
{%- if cookiecutter.provider == "aws" %}
    aws = {
      source = "hashicorp/aws"
      version = "3.64.2"
    }
{%- elif cookiecutter.provider == "azure" %}
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=2.44.0"
    }
{%- elif cookiecutter.provider == "gcp" %}
    google = {
      source = "hashicorp/google"
      version = "=3.89.0"
    }
{%- elif cookiecutter.provider == "do" %}
    digitalocean = {
      source = "digitalocean/digitalocean"
      version = "=2.14.0"
    }
{% endif %}
  }
  required_version = ">=1.0"
}
