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

variable "storage" {
  description = "Storage configuration for backup-restore server"
  type = object({
    type   = string
    config = map(string)
  })
}

variable "image" {
  description = "The image to use for the backup-restore service"
  type        = string
}

variable "image_tag" {
  description = "The tag of the image to use for the backup-restore service"
  type        = string
}
