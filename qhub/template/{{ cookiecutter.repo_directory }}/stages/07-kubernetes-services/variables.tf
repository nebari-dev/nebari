variable "name" {
  type    = string
  default = "{{ cookiecutter.project_name }}"
}

variable "environment" {
  type    = string
  default = "{{ cookiecutter.namespace }}"
}

variable "endpoint" {
  description = "endpoint"
  type        = string
  default     = "{{ cookiecutter.domain }}"
}

variable "realm_id" {
  description = "Keycloak realm id for creating clients"
  type        = string
}

variable "cdsdashboards" {
  description = "Enable CDS Dashboards"
  type        = object({
    enabled = bool
    cds_hide_user_named_servers = bool
    cds_hide_user_dashboard_servers = bool
  })
  default     = {
    enabled = true
    cds_hide_user_named_servers = true
    cds_hide_user_dashboard_servers = false
  }
}

variable "jupyterhub-theme" {
  description = "JupyterHub theme"
  type        = map
  default     = {}
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

variable "dask-gateway-image" {
  description = "Dask worker image"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "{{ cookiecutter.default_images.dask_gateway.split(':')[0] }}"
    tag  = "{{ cookiecutter.default_images.dask_gateway.split(':')[1] }}"
  }
}

variable "conda-store-image" {
  description = "Conda-store image"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "{{ cookiecutter.default_images.conda_store.split(':')[0] }}"
    tag  = "{{ cookiecutter.default_images.conda_store.split(':')[1] }}"
  }
}

{% if cookiecutter.prefect.enabled -%}
variable "prefect_token" {
  type = string
}
{%- endif %}
