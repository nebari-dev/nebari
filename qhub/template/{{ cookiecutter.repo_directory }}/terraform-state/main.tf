{% if cookiecutter.provider == "aws" -%}
provider "aws" {
  region = "{{ cookiecutter.amazon_web_services.region }}"
}

module "terraform-state" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/aws/terraform-state?ref=azure"

  name = "{{ cookiecutter.project_name }}"

  tags = {
    Organization = "{{ cookiecutter.project_name }}"
    Project      = "terraform-state"
    Environment  = "dev"
  }
}
{% elif cookiecutter.provider == "gcp" -%}
provider "google" {
  project = "{{ cookiecutter.google_cloud_platform.project }}"
  region  = "{{ cookiecutter.google_cloud_platform.region }}"
  zone    = "{{ cookiecutter.google_cloud_platform.zone }}"
}

module "terraform-state" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/gcp/terraform-state?ref=azure"

  name     = "{{ cookiecutter.project_name }}"
  location = "{{ cookiecutter.google_cloud_platform.region }}"
}
{% elif cookiecutter.provider == "azure" -%}
provider "azurerm" {
  version = "=2.44.0"
  features {} 
}

module "terraform-state" {
  source = "github.com/quansight/qhub-terraform-modules//modules/azure/terraform-state?ref=azure"

  name     = "{{ cookiecutter.project_name }}"
  location = "{{ cookiecutter.azure.region }}"
  storage_account_postfix = "{{ cookiecutter.azure.storage_account_postfix }}"
}
{% elif cookiecutter.provider == "do" -%}
module "terraform-state" {
  source = "{{ cookiecutter.terraform_modules.repository }}//modules/digitalocean/terraform-state?ref=azure"

  name   = "{{ cookiecutter.project_name }}"
  region = "{{ cookiecutter.digital_ocean.region }}"
}
{% endif %}
