variable "namespace" {
  description = "deploy keda server on this namespace"
  type        = string
  default     = "dev"
}

variable "general_node_selector" {
  description = "General node group selector."
}
