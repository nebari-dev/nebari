{%- if cookiecutter.provider == "aws" %}
terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
  required_version = ">= 0.13"
}
{%- elif cookiecutter.provider == "gcp" %}
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
  }
  required_version = ">= 0.13"
}
{%- elif cookiecutter.provider == "azure" %}
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=2.44.0"
    }
  }
  required_version = ">= 0.13"
}
{% endif %}
