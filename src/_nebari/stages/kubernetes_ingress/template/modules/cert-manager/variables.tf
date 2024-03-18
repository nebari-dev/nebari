variable "namespace_name" {
  default = "dev"
}

variable "chart_version" {
  type        = string
  description = "HELM Chart Version for cert-manager"
  default     = "1.14.4"
}

variable "acme-email" {
  default = ""
}

variable "acme-server" {
  default = ""
}
