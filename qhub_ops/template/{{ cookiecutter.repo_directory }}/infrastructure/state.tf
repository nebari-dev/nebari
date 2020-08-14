{% if cookiecutter.provider == "aws" -%}
terraform {
  backend "s3" {
    bucket         = "{{ cookiecutter.project_name }}-terraform-state"
    key            = "terraform/{{ cookiecutter.project_name }}.tfstate"
    region         = "{{ cookiecutter.amazon_web_services.region }}"
    encrypt        = true
    dynamodb_table = "{{ cookiecutter.project_name }}-terraform-state-lock"
  }
}
{% elif cookiecutter.provider == "gcp" -%}
terraform {
  backend "gcs" {
    bucket = "{{ cookiecutter.project_name }}-terraform-state"
    prefix = "terraform/{{ cookiecutter.project_name }}"
  }
}
{% elif cookiecutter.provider == "do" -%}
terraform {
  backend "s3" {
    endpoint                    = "{{ cookiecutter.digital_ocean.region }}.digitaloceanspaces.com"
    region                      = "us-west-1" # fake aws region required by terraform
    bucket                      = "{{ cookiecutter.project_name }}-terraform-state"
    key                         = "terraform/{{ cookiecutter.project_name }}.tfstate"
    skip_requesting_account_id  = true
    skip_credentials_validation = true
    skip_get_ec2_platforms      = true
    skip_metadata_api_check     = true
  }
}
{% endif -%}
