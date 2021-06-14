variable "name" {
  description = "Prefix name form conda-store server kubernetes resource"
  type        = string
}

variable "namespace" {
  description = "Namespace to deploy conda-store server"
  type        = string
}

variable "nfs_capacity" {
  description = "Capacity of conda-store deployment"
  type        = string
  default     = "10Gi"
}

variable "environments" {
  description = "conda environments for conda-store to build"
  type        = map(any)
  default     = {}
}

variable "node-group" {
  description = "Node key value pair for bound general resources"
  type = object({
    key   = string
    value = string
  })
}

variable "conda-store-image" {
  description = "Conda-store image"
  type = object({
    name = string
    tag  = string
  })
}
