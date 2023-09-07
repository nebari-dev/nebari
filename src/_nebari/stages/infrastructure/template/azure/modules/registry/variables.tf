variable "name" {
  description = "Prefix name to azure container registry"
  type        = string
}

variable "location" {
  description = "Location of nebari resource group"
  type        = string
}

variable "resource_group_name" {
  description = "name of nebari resource group"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
