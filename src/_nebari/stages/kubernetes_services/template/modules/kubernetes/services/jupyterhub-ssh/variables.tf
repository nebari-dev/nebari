variable "name" {
  description = "name prefix to assign to jupyterhub-ssh"
  type        = string
  default     = "nebari"
}

variable "namespace" {
  description = "namespace to deploy jupyterhub-ssh"
  type        = string
}

variable "node-group" {
  description = "Node group to associate jupyterhub-ssh deployment"
  type = object({
    key   = string
    value = string
  })
}

variable "jupyterhub_api_url" {
  description = "jupyterhub api url for jupyterhub-ssh"
  type        = string
}

variable "jupyterhub-ssh-image" {
  description = "image to use for jupyterhub-ssh"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "quay.io/jupyterhub-ssh/ssh"
    tag  = "0.0.1-0.dev.git.149.he5107a4"
  }
}

variable "jupyterhub-sftp-image" {
  description = "image to use for jupyterhub-sftp"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "quay.io/jupyterhub-ssh/sftp"
    tag  = "0.0.1-0.dev.git.142.h402a3d6"
  }
}

variable "persistent_volume_claim" {
  description = "name of persistent volume claim to mount"
  type = object({
    name = string
    id   = string
  })
}
