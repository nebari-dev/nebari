variable "name" {
  description = "Prefix name form conda-store server kubernetes resource"
  type        = string
}

variable "namespace" {
  description = "Namespace to deploy conda-store server"
  type        = string
}

variable "nfs_capacity" {
  description = "Capacity of conda-store filesystem"
  type        = string
  default     = "10Gi"
}

variable "minio_capacity" {
  description = "Capacity of conda-store object storage"
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
  description = "Conda-Store image"
  type        = string
  default     = "quansight/conda-store-server"
}

variable "conda-store-image-tag" {
  description = "Version of conda-store to use"
  type        = string
}

variable "external-url" {
  description = "External url that jupyterhub cluster is accessible"
  type        = string
}

variable "realm_id" {
  description = "Keycloak realm to use for deploying openid client"
  type        = string
}

variable "extra-settings" {
  description = "Additional traitlets settings to apply before extra-config traitlets code is run"
  type        = map(any)
  default     = {}
}

variable "extra-config" {
  description = "Additional traitlets configuration code to be ran"
  type        = string
  default     = ""
}

variable "default-namespace-name" {
  description = "Name of the default conda-store namespace"
  type        = string
}

variable "services" {
  description = "Map of services tokens and scopes for conda-store"
  type        = map(any)
}

variable "conda-store-fs" {
  type        = string
  description = "Use NFS or Ceph"

  validation {
    condition     = contains(["cephfs", "nfs"], var.conda-store-fs)
    error_message = "Allowed values for input_parameter are \"cephfs\", or \"nfs\"."
  }
}
