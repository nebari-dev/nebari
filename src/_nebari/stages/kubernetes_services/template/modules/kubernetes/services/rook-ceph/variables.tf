variable "namespace" {
  description = "deploy rook-ceph operator in this namespace"
  type        = string
}

variable "operator_namespace" {
  description = "namespace where the rook-ceph operator is deployed"
  type        = string
}


variable "overrides" {
  description = "Rook Ceph helm chart overrides"
  type        = list(string)
  default     = []
}

variable "storage_class_name" {
  description = "Name of the storage class to create"
  type        = string
  default     = null
}

variable "node_group" {
  description = "Node key value pair for bound resources"
  type = object({
    key   = string
    value = string
  })
}

variable "ceph_storage_capacity" {
  description = "Ceph storage capacity in Gi"
  type        = number
}
