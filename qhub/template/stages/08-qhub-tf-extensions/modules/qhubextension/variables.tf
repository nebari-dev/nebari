variable "namespace" {
  description = "Namespace to deploy into"
  type        = string
}

variable "name" {
  description = "Name of extension"
  type        = string
}

variable "external-url" {
  description = "URL of the QHub"
  type        = string
}

variable "image" {
  description = "Docker image for extension"
  type        = string
}

variable "urlslug" {
  description = "Slug for URL"
  type        = string
}

variable "private" {
  description = "Protect behind login page"
  type        = bool
  default     = true
}

variable "oauth2client" {
  description = "Create a Keycloak client and include env vars"
  type        = bool
  default     = false
}

variable "keycloakadmin" {
  description = "Include env vars for a keycloak admin user to make Keycloak Admin API calls"
  type        = bool
  default     = false
}

variable "jwt" {
  description = "Create secret and cookie name for JWT, set as env vars"
  type        = bool
  default     = false
}

variable "qhubconfigyaml" {
  description = "Mount qhub-config.yaml from configmap"
  type        = bool
  default     = false
}

variable "envs" {
  description = "List of env var objects"
  type        = list(map(any))
  default     = []
}

variable "qhub-realm-id" {
  description = "Keycloak qhub realm id"
  type        = string
  default     = ""
}

variable "keycloak_qhub_bot_password" {
  description = "Keycloak client password"
  type        = string
  default     = ""
}
