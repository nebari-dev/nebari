variable "namespace" {
  description = "Namespace for helm chart resource"
  type        = string
}

variable "overrides" {
  description = "Helm overrides to apply"
  type        = list(string)
  default     = []
}
