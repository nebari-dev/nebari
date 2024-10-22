variable "backup-restore-image" {
  description = "The image to use for the backup-restore service"
  default     = "vcerutti/nebari-backup-restore"
}

variable "backup-restore-image-tag" {
  description = "The tag of the image to use for the backup-restore service"
  default     = "latest"
}

variable "backup-restore-clients" {
  description = "List of clients that can access the backup-restore server by API"
  type        = list(string)
  default     = ["nebari-cli"]
}

module "kubernetes-backup-restore-server" {
  source = "./modules/kubernetes/services/backup-restore"

  name      = "nebari"
  namespace = var.environment

  external-url = var.endpoint
  realm_id     = var.realm_id

  backup-restore-image     = var.backup-restore-image
  backup-restore-image-tag = var.backup-restore-image-tag
  clients                  = var.backup-restore-clients
}
