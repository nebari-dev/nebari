variable "postgresql_additional_users" {
  description = "Additional Postgresql users"
  type = list(object({
    username = string
    password = string
    database = string
  }))
  default = []
}

variable "postgresql_extensions" {
  description = "Postgresql extensions to enable"
  type        = list(string)
  default     = []
}
