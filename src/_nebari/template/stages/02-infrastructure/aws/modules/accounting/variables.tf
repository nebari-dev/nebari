variable "project" {
  description = "Project for resource group filter"
  type        = string
}

variable "environment" {
  description = "Environment for resource group filter"
  type        = string
}

variable "tags" {
  description = "Additional tags to apply to all network resource"
  type        = map(string)
  default     = {}
}
