variable "name" {
  description = "name for nebari deployment"
  type        = string
}

variable "namespace" {
  description = "Namespace for jupyterhub deployment"
  type        = string
}

variable "overrides" {
  description = "Jupyterhub helm chart list of overrides"
  type        = list(string)
  default     = []
}

variable "jupyterhub-image" {
  description = "Docker image to use for jupyterhub hub"
  type = object({
    name = string
    tag  = string
  })
}

variable "jupyterlab-image" {
  description = "Docker image to use for jupyterlab users"
  type = object({
    name = string
    tag  = string
  })
}

variable "general-node-group" {
  description = "Node key value pair for bound general resources"
  type = object({
    key   = string
    value = string
  })
}

variable "user-node-group" {
  description = "Node group key value pair for bound user resources"
  type = object({
    key   = string
    value = string
  })
}

variable "home-pvc" {
  description = "Name for persistent volume claim to use for home directory uses /home/{username}"
  type        = string
}

variable "shared-pvc" {
  description = "Name for persistent volume claim to use for shared directory uses /share/{group}"
  type        = string
}

variable "conda-store-pvc" {
  description = "Name for persistent volume claim to use for conda-store directory"
  type        = string
}

variable "conda-store-mount" {
  description = "Mount directory for conda-store environments"
  type        = string
}

variable "extra-mounts" {
  description = "Name of additional configmaps and pvcs to be mounted within jupyterlab image"
  default     = {}
}

variable "external-url" {
  description = "External url that jupyterhub cluster is accessible"
  type        = string
}

variable "realm_id" {
  description = "Keycloak realm to use for deploying openid client"
  type        = string
}

variable "services" {
  description = "Set of services that use the jupyterhub api"
  type        = set(string)
}

variable "theme" {
  description = "JupyterHub theme"
  type        = map(any)
  default     = {}
}

variable "profiles" {
  description = "JupyterHub profiles"
  default     = []
}

variable "conda-store-service-name" {
  description = "Name of conda-store service"
  type        = string
}

variable "conda-store-environments" {
  description = "conda environments from conda-store in filesystem namespace"
  type        = any
  default     = {}
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

variable "default-conda-store-namespace" {
  description = "Default conda-store namespace"
  type        = string
}

variable "idle-culler-settings" {
  description = "Idle culler timeout settings (in minutes)"
  type = object({
    kernel_cull_busy                    = bool
    kernel_cull_connected               = bool
    kernel_cull_idle_timeout            = number
    kernel_cull_interval                = number
    server_shutdown_no_activity_timeout = number
    terminal_cull_inactive_timeout      = number
    terminal_cull_interval              = number
  })
}
