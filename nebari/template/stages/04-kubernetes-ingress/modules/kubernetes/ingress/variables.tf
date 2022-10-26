variable "name" {
  description = "name prefix to assign to traefik"
  type        = string
  default     = "nebari"
}

variable "namespace" {
  description = "namespace to deploy traefik"
  type        = string
}

variable "node-group" {
  description = "Node group to associate ingress deployment"
  type = object({
    key   = string
    value = string
  })

}

variable "traefik-image" {
  description = "traefik image to use"
  type = object({
    image = string
    tag   = string
  })
}

variable "loglevel" {
  description = "traefik log level"
  default     = "WARN"
}

variable "acme-email" {
  description = "ACME server email"
  default     = "costrouchov@quansight.com"
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
  type        = string
  default     = null
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
