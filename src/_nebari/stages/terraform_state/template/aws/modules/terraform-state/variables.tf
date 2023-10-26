variable "name" {
  description = "Prefix of name to append resource"
  type        = string
}

variable "tags" {
  description = "Additional tags to apply to resource"
  type        = map(string)
  default     = {}
}
