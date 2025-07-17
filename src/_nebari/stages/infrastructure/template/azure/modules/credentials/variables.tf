variable "azure_rbac_enabled" {
  description = "Flag to enable Azure RBAC"
  type        = bool
}

variable "kube_admin_config" {
  description = "Kube admin config for RBAC"
  type        = any
  sensitive   = true
}

variable "kube_config" {
  description = "Kube config for standard access"
  type        = any
  sensitive   = true
}
