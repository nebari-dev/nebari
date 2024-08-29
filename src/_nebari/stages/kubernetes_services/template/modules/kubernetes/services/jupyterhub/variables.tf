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
  type = object({
    name = string
    id   = string
  })
}

variable "shared-pvc" {
  description = "Name for persistent volume claim to use for shared directory uses /share/{group}"
  type = object({
    name = string
    id   = string
  })
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

variable "conda-store-jhub-apps-token" {
  description = "Token for conda-store to be used by jhub apps for fetching conda environments dynamically."
  type        = string
}

variable "conda-store-environments" {
  description = "conda environments from conda-store in filesystem namespace"
  type        = any
  default     = {}
}

variable "jhub-apps-enabled" {
  description = "Enable/Disable JupyterHub Apps extension to spin up apps, dashboards, etc"
  type        = bool
}

variable "conda-store-argo-workflows-jupyter-scheduler-token" {
  description = "Token for argo-workflows-jupyter-schedule to use conda-store"
  type        = string
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

variable "argo-workflows-enabled" {
  description = "Enable Argo Workflows"
  type        = bool
}

variable "jupyterlab-default-settings" {
  description = "Default settings for JupyterLab to be placed in overrides.json"
  type        = map(any)
}

variable "jupyterlab-gallery-settings" {
  description = "Server-side settings for jupyterlab-gallery extension"
  type = object({
    title                         = optional(string)
    destination                   = optional(string)
    hide_gallery_without_exhibits = optional(bool)
    exhibits = list(object({
      git         = string
      title       = string
      homepage    = optional(string)
      description = optional(string)
      icon        = optional(string)
      account     = optional(string)
      token       = optional(string)
      branch      = optional(string)
      depth       = optional(number)
    }))
  })
}

variable "jupyterlab-pioneer-enabled" {
  description = "Enable JupyterLab Pioneer for telemetry"
  type        = bool
}

variable "jupyterlab-pioneer-log-format" {
  description = "Logging format for JupyterLab Pioneer"
  type        = string
}

variable "jupyterlab-preferred-dir" {
  description = "Directory in which the JupyterLab should open the file browser"
  type        = string
}

variable "cloud-provider" {
  description = "Name of cloud provider."
  type        = string
}

variable "initial-repositories" {
  description = "Map of folder location and git repo url to clone"
  type        = string
  default     = "[]"
}
