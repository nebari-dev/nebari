variable "name" {
  type    = string
  default = "{{ cookiecutter.project_name }}"
}

variable "environment" {
  type    = string
  default = "dev"
}

{% if cookiecutter.provider == "aws" %}
variable "region" {
  type    = string
  default = "{{ cookiecutter.amazon_web_services.region }}"
}

variable "availability_zones" {
  description = "AWS availability zones within AWS region"
  type        = list(string)
  default     = {{ cookiecutter.amazon_web_services.availability_zones | jsonify }}
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
  default     = {{ cookiecutter.google_cloud_platform.availability_zones | jsonify }}
}
{% elif cookiecutter.provider == "do" %}
variable "region" {
  type    = string
  default = "{{ cookiecutter.digital_ocean.region }}"
}
{% endif -%}

# jupyterhub
variable "endpoint" {
  description = "Jupyterhub endpoint"
  type        = string
  default     = "jupyter.{{ cookiecutter.domain }}"
}

variable "jupyterhub-image" {
  description = "Jupyterhub user image"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "quansight/qhub-jupyterhub"
    tag  = "588d50b4ab0c4fee6c06e40144a16f3a4b16e0cf"
  }
}

variable "jupyterlab-image" {
  description = "Jupyterlab user image"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "quansight/qhub-jupyterlab"
    tag  = "588d50b4ab0c4fee6c06e40144a16f3a4b16e0cf"
  }
}

variable "dask-worker-image" {
  description = "Dask worker image"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "quansight/qhub-dask-worker"
    tag  = "588d50b4ab0c4fee6c06e40144a16f3a4b16e0cf"
  }
}
