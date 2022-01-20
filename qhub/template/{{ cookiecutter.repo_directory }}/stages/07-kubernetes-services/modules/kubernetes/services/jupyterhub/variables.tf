variable "namespace" {
  description = "Namespace for jupyterhub deployment"
  type        = string
}

variable "overrides" {
  description = "Jupyterhub helm chart list of overrides"
  type        = list(string)
  default     = []
}

variable "home-pvc" {
  description = "Name for persistent volume claim to use for home directory uses /home/{username}"
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
