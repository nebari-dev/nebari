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

variable "conda-store-default-namespace" {
  description = "Default conda-store namespace name"
  type        = string
  default     = "nebari-git"
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

variable "terminal_cull_inactive_timeout" {
  description = "Timeout (in minutess) in which a terminal has been inactive and ready to be culled"
  type        = number
}

variable "terminal_cull_interval" {
  description = "The interval (in minutes) on which to check for terminals exceeding the inactive timeout value"
  type        = number
}

variable "kernel_cull_idle_timeout" {
  description = "Timeout (in minutes) after which an idle kernel is considered ready to be culled"
  type        = number
}

variable "kernel_cull_interval" {
  description = "The interval (in minutes) on which to check for idle kernels exceeding the cull timeout value"
  type        = number
}

variable "kernel_cull_connected" {
  description = "Whether to consider culling kernels which have one or more connections"
  type        = bool
}

variable "kernel_cull_busy" {
  description = "Whether to consider culling kernels which are currently busy running some code"
  type        = bool
}

variable "server_shutdown_no_activity_timeout" {
  description = "Shut down the server after N minutes with no kernels or terminals running and no activity"
  type        = number
}
