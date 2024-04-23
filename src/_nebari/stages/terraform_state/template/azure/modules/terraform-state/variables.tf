variable "resource_group_name" {
  description = "Prefix of name to append resource"
  type        = string
}

variable "name" {
  description = "Prefix of name to append resource"
  type        = string
}

variable "location" {
  description = "Location for terraform state"
  type        = string
}

variable "storage_account_name" {
  description = "Name for terraform state storage account, must be unique across Azure, 3-24 characters long and only include lowercase letters and numbers"
  type        = string
}

variable "storage_container_name" {
  description = "Name for terraform state storage container"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
