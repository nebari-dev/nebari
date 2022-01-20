variable "name" {
  type    = string
  default = "{{ cookiecutter.project_name }}"
}

variable "environment" {
  type    = string
  default = "{{ cookiecutter.namespace }}"
}
