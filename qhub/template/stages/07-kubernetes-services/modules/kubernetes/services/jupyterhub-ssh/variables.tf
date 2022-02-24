variable "name" {
  description = "name prefix to assign to jupyterhub-ssh"
  type        = string
  default     = "qhub"
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
    name = "yuvipanda/jupyterhub-ssh-ssh"
    tag  = "0.0.1-n026.hf136ec7"
  }
}

variable "jupyterhub-sftp-image" {
  description = "image to use for jupyterhub-sftp"
  type = object({
    name = string
    tag  = string
  })
  default = {
    name = "yuvipanda/jupyterhub-ssh-sftp"
    tag  = "0.0.1-n026.hf136ec7"
  }
}

variable "persistent_volume_claim" {
  description = "name of persistent volume claim to mount"
  type        = string
}
