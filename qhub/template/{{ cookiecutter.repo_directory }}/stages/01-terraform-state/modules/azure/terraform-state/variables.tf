variable "resource_group_name" {
  description = "Prefix name for terraform state"
  type        = string
}

variable "location" {
  description = "Location for terraform state"
  type        = string
}

variable "storage_account_postfix" {
  description = "random characters appended to storage account name to facilitate global uniqueness"
  type        = string
}
