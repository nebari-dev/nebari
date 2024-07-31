variable "name" {
  description = "Prefix name form nfs mount kubernetes resource"
  type        = string
}

variable "namespace" {
  description = "Namespace to deploy nfs storage mount"
  type        = string
}

variable "fs_capacity" {
  description = "Capacity of NFS server mount in Gi"
  type        = number
  default     = 10
}

variable "ceph-pvc-name" {
  description = "Name of the persistent volume claim"
  type        = string
}
