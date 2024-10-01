variable "name" {
  description = "Name prefix to deploy backup-restore server"
  type        = string
  default     = "nebari"
}

variable "namespace" {
  description = "Namespace to deploy backup-restore server"
  type        = string
}

variable "external-url" {
  description = "External url that jupyterhub cluster is accessible"
  type        = string
}

variable "clients" {
  description = "List of clients that can access the backup-restore server by API"
  type        = list(string)
}
