variable "external-url" {
  description = "External public url that cluster is accessible"
  type        = string
}

variable "name" {
  description = "Project name for the QHub deployment"
  type        = string
}

variable "users" {
  description = "list of users data"
  type        = list(map(any))
  default     = []
}

variable "groups" {
  description = "list of groups data"
  type        = list(map(any))
  default     = []
}
