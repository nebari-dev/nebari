variable "name" {
  description = "name prefix to assign to traefik"
  type        = string
  default     = "qhub"
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
  default = {
    image = "traefik"
    tag   = "2.4.8"
  }
}

variable "loglevel" {
  description = "traefik log level"
  default     = "WARN"
}

variable "enable-certificates" {
  description = "Enable certificates"
  default     = false
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
