variable "realm" {
  description = "Keycloak realm to use for nebari"
  type        = string
}

variable "realm_display_name" {
  description = "Keycloak realm display name for nebari"
  type        = string
}

variable "keycloak_groups" {
  description = "Permission groups in keycloak used for granting access to services"
  type        = set(string)
  default     = []
}

variable "authentication" {
  description = "Authentication configuration for keycloak"
  type        = any
}

variable "default_groups" {
  description = "Set of groups that should exist by default"
  type        = set(string)
  default     = []
}
