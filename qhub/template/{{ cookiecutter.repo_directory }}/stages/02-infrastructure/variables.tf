variable "name" {
  type    = string
  default = "{{ cookiecutter.project_name }}"
}

variable "environment" {
  type    = string
  default = "{{ cookiecutter.namespace }}"
}

{% if cookiecutter.provider == "aws" %}
variable "region" {
  type    = string
  default = "{{ cookiecutter.amazon_web_services.region }}"
}

variable "availability_zones" {
  description = "AWS availability zones within AWS region"
  type        = list(string)
  default     = {{ cookiecutter.amazon_web_services.availability_zones | default([],true) | jsonify }}
}

variable "vpc_cidr_block" {
  description = "VPC cidr block for infastructure"
  type        = string
  default     = "10.10.0.0/16"
}
{% elif cookiecutter.provider == "gcp" %}
variable "region" {
  type    = string
  default = "{{ cookiecutter.google_cloud_platform.region }}"
}

variable "availability_zones" {
  description = "GCP availability zones within region"
  type        = list(string)
  default     = {{ cookiecutter.google_cloud_platform.availability_zones | default([],true) | jsonify }}
}
{% elif cookiecutter.provider == "azure" %}
variable "region" {
  description = "azure location"
  type        = string
  default     = "{{ cookiecutter.azure.region }}"
}
{% elif cookiecutter.provider == "do" %}
variable "region" {
  type    = string
  default = "{{ cookiecutter.digital_ocean.region }}"
}
{% endif -%}
