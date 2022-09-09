variable "name" {
  description = "Prefix name to assign to ingress kubernetes resources"
  type        = string
}

variable "environment" {
  description = "Kubernetes namespace to deploy ingress resources"
  type        = string
}

variable "node_groups" {
  description = "Node group selectors for kubernetes resources"
  type = map(object({
    key   = string
    value = string
  }))
}

variable "acme-email" {
  description = "ACME server email"
  default     = "qhub@example.com"
}

variable "acme-server" {
  description = "ACME server"
  # for testing use the letencrypt staging server
  #  - staging:    https://acme-staging-v02.api.letsencrypt.org/directory
  #  - production: https://acme-v02.api.letsencrypt.org/directory
  default = "https://acme-staging-v02.api.letsencrypt.org/directory"
}

variable "certificate-secret-name" {
  description = "Kubernetes secret used for certificate"
  default     = ""
}


variable "load-balancer-ip" {
  description = "IP Address of the load balancer"
  type        = string
  default     = null
}


variable "load-balancer-annotations" {
  description = "Annotations for the load balancer"
  type        = map(string)
  default     = null
}


variable "certificate-service" {
  description = "The certificate service to use"
  type        = string
  default     = "self-signed"
}


variable "additional-arguments" {
  description = "Additional command line arguments to supply to traefik ingress"
  type        = list(string)
  default     = []
}
