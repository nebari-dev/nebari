variable "namespace" {
  description = "Namespace for all resources deployed"
  type        = string
}

variable "labels" {
  description = "Additional labs to apply for all resources deployed"
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "map of with map of key value secrets to store in kubernetes secrets"
  type = list(object({
    name = string
    data = map(string)
  }))
  default = []
}
