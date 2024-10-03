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

variable "realm_id" {
  description = "Realm ID to use for authentication"
  type        = string
}

variable "backup-restore-image" {
  description = "Backup-restore image"
  type        = string
}

variable "backup-restore-image-tag" {
  description = "Version of backup-restore to use"
  type        = string
}
