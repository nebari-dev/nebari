variable "namespace" {
  description = "Namespace to deploy forwardauth"
  type        = string
}

variable "external-url" {
  description = "External domain where QHub is accessible"
  type        = string
}

variable "jh-client-id" {
  description = "JupyterHub service client ID"
  type        = string
}

variable "jh-client-secret" {
  description = "JupyterHub service client secret"
  type        = string
}

variable "callback-url-path" {
  description = "Path of Callback URL"
  type        = string
}