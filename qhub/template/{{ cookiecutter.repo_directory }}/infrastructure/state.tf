{% if cookiecutter.provider == "aws" and cookiecutter.terraform_state.type == "remote" -%}
terraform {
  backend "s3" {
    bucket         = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}-terraform-state"
    key            = "terraform/{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}.tfstate"
    region         = "{{ cookiecutter.amazon_web_services.region }}"
    encrypt        = true
    dynamodb_table = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}-terraform-state-lock"
  }
}
{% elif cookiecutter.provider == "gcp" and cookiecutter.terraform_state.type == "remote" -%}
terraform {
  backend "gcs" {
    bucket = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}-terraform-state"
    prefix = "terraform/{{ cookiecutter.project_name }}"
  }
}
{% elif cookiecutter.provider == "do" and cookiecutter.terraform_state.type == "remote" -%}
terraform {
  backend "s3" {
    endpoint                    = "{{ cookiecutter.digital_ocean.region }}.digitaloceanspaces.com"
    region                      = "us-west-1" # fake aws region required by terraform
    bucket                      = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}-terraform-state"
    key                         = "terraform/{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}.tfstate"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
  }
}
{% elif cookiecutter.provider == "azure" and cookiecutter.terraform_state.type == "remote" -%}

terraform {
  backend "azurerm" {
    resource_group_name = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}"
    # storage account must be globally unique
    storage_account_name = "{{ cookiecutter.project_name }}{{ cookiecutter.namespace }}{{ cookiecutter.azure.storage_account_postfix }}"
    container_name       = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}state"
    key                  = "terraform/{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}.tfstate"
  }
}
{% elif cookiecutter.provider == "local" and cookiecutter.terraform_state.type == "remote" -%}
terraform {
  backend "kubernetes" {
    secret_suffix    = "{{ cookiecutter.project_name }}-{{ cookiecutter.namespace }}-terraform-state"
    load_config_file = true
{% if cookiecutter.local.kube_context is defined %}
    config_context = "{{ cookiecutter.local.kube_context }}"
{% endif %}
  }
}
{% elif cookiecutter.terraform_state.type == "existing" %}
terraform {
  backend "{{ cookiecutter.terraform_state.backend }}" {
{% for key, value in cookiecutter.terraform_state.config.items() %}
    {{ "%-10s" | format(key) }} = "{{ value }}"
{% endfor %}
  }
}
{%- endif -%}
