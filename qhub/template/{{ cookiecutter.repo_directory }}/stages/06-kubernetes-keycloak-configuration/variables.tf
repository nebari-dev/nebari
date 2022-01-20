variable "name" {
  type    = string
  default = "{{ cookiecutter.project_name }}"
}

variable "environment" {
  type    = string
  default = "{{ cookiecutter.namespace }}"
}

variable "realm" {
  description = "Keycloak realm to use for QHub"
  type        = string
  default     = "qhub-{{ cookiecutter.project_name }}"
}

variable "keycloak_groups" {
  description = "Permission groups in keycloak used for granting access to services"
  type = set(string)
  default = ["admin", "developer", "viewer"]
}
