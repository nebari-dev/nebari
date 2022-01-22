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
