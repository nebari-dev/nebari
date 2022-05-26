variable "name" {
  description = "name prefix to assign to kbatch"
  type        = string
  default     = "qhub"
}

variable "jupyterhub_api_token" {
  type    = string
  default = ""
}

variable "namespace" {
  type    = string
  default = "dev"
}

variable "image" {
  type    = string
  default = ""
}

variable "node-group" {
  description = "Node key value pair for bound resources"
  type = object({
    key   = string
    value = string
  })
}

variable "external-url" {
  description = "External url that jupyterhub cluster is accessible"
  type        = string
}

variable "overrides" {
  description = "kbatch helm chart list of overrides"
  type        = list(string)
  default     = []
}

variable "dask-gateway-address" {
  description = "Dask Gateway address"
  type        = string
}

variable "dask-gateway-proxy-address" {
  description = "Dask Gateway proxy-address"
  type        = string
}

variable "dask-worker-image" {
  description = "Dask worker image"
  type = object({
    name = string
    tag  = string
  })
}
