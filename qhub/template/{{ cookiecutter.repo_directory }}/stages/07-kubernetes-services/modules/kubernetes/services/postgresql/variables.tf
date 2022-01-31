variable "name" {
  description = "Name prefix to deploy conda-store server"
  type        = string
  default     = "qhub"
}


variable "namespace" {
  description = "Namespace to deploy conda-store server"
  type        = string
}


variable "database" {
  description = "Postgres database"
  type        = string
}


variable "overrides" {
  description = "Postgresql helm chart list of overrides"
  type        = list(string)
  default     = []
}

variable "node-group" {
  description = "Node key value pair for bound general resources"
  type = object({
    key   = string
    value = string
  })
}
