variable "backup-restore-enabled" {
  description = "Enable backup-restore service"
  type        = bool
  default     = false
}

variable "backup-restore-storage" {
  description = "Storage backend for backup-restore"
  type        = map(string)
  default     = {}
}

variable "backup-restore-image" {
  description = "The image to use for the backup-restore service"
  type        = string
}

variable "backup-restore-image-tag" {
  description = "The tag of the image to use for the backup-restore service"
  type        = string
}

module "nebari-backup-restore" {
  count  = var.backup-restore-enabled ? 1 : 0
  source = "./modules/kubernetes/services/backup-restore"

  external-url = var.endpoint
  realm_id     = "nebari"
  image        = var.backup-restore-image
  storage      = var.backup-restore-storage
  image_tag    = var.backup-restore-image-tag
  namespace    = var.environment
  clients      = ["nebari-cli"]
}
