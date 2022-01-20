variable "name" {
  type    = string
  default = "{{ cookiecutter.project_name }}"
}

variable "environment" {
  type    = string
  default = "{{ cookiecutter.namespace }}"
}

variable "endpoint" {
  description = "QHub cluster endpoint"
  type        = string
  default     = "{{ cookiecutter.domain }}"
}
