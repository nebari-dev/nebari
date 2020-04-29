{% if cookiecutter.provider == "aws" -%}
provider "aws" {
  region = "{{ cookiecutter.amazon_web_services.region }}"
}

module "terraform-state" {
  source = "github.com/quansight/qhub-terraform-modules//modules/aws/terraform-state"

  name   = "{{ cookiecutter.project_name }}"

  tags = {
    Organization = "{{ cookiecutter.project_name }}"
    Project      = "terraform-state"
    Environment  = "dev"
  }
}
{% elif cookiecutter.provider == "gcp" -%}
provider "google" {
  project     = "{{ cookiecutter.google_cloud_platform.project }}"
  region      = "{{ cookiecutter.google_cloud_platform.region }}"
  zone        = "{{ cookiecutter.google_cloud_platform.zone }}"
}

module "terraform-state" {
  source = "github.com/quansight/qhub-terraform-modules//modules/gcp/terraform-state"

  name     = "{{ cookiecutter.project_name }}"
  location = "{{ cookiecutter.google_cloud_platform.region }}"
}
{% elif cookiecutter.provider == "do" -%}
module "terraform-state" {
  source = "github.com/quansight/qhub-terraform-modules//modules/digitalocean/terraform-state"

  name   = "{{ cookiecutter.project_name }}"
  region = "{{ cookiecutter.digital_ocean.region }}"
}
{% endif %}
