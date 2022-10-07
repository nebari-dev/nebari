variable "name" {
  description = "Prefix name to assign to kubernetes resources"
  type        = string
}

variable "environment" {
  description = "Kubernetes namespace to create resources within"
  type        = string
}

variable "endpoint" {
  description = "Endpoint for services"
  type        = string
}

variable "realm_id" {
  description = "Keycloak realm id for creating clients"
  type        = string
}

variable "node_groups" {
  description = "Node group selectors for kubernetes resources"
  type = map(object({
    key   = string
    value = string
  }))
}

variable "jupyterhub-logout-redirect-url" {
  description = "Next redirect destination following a Keycloak logout"
  type        = string
  default     = ""
}

variable "jupyterhub-hub-extraEnv" {
  description = "Extracted overrides to merge with jupyterhub.hub.extraEnv"
  type        = string
  default     = "[]"
}

variable "conda-store-service-token-scopes" {
  description = "Map of services tokens and scopes for conda-store"
  type        = map(any)
  default = {
    "cdsdashboards" = {
      "primary_namespace" : "cdsdashboards",
      "role_bindings" : {
        "*/*" : ["viewer"],
      }
    }
  }
}
