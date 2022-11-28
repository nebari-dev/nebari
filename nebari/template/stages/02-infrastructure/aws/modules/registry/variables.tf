variable "name" {
  description = "Prefix AWS registry name"
  type        = string
}

variable "tags" {
  description = "AWS ECR Registry tags"
  type        = map(string)
  default     = {}
}
