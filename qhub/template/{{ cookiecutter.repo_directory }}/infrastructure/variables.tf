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
{% elif cookiecutter.provider == "azure" %}
variable "region" {
  description = "azure location"
  type    = string
  default = "{{ cookiecutter.azure.region }}"
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
    name = "{{ cookiecutter.default_images.jupyterhub.split(':')[0] }}"
    tag  = "{{ cookiecutter.default_images.jupyterhub.split(':')[1] }}"
  }
}

variable "jupyterlab-image" {
  description = "Jupyterlab user image"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "{{ cookiecutter.default_images.jupyterlab.split(':')[0] }}"
    tag  = "{{ cookiecutter.default_images.jupyterlab.split(':')[1] }}"
  }
}

variable "dask-worker-image" {
  description = "Dask worker image"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "{{ cookiecutter.default_images.dask_worker.split(':')[0] }}"
    tag  = "{{ cookiecutter.default_images.dask_worker.split(':')[1] }}"
  }
}

{% if cookiecutter.prefect is true -%}
variable "prefect_token" {
  type = string
}
{%- endif %}
