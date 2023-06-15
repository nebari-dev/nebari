variable "name" {
  description = "Prefix name to assign to keycloak kubernetes resources"
  type        = string
}

variable "environment" {
  description = "Kubernetes namespace to deploy keycloak"
  type        = string
}

variable "endpoint" {
  description = "nebari cluster endpoint"
  type        = string
}

variable "initial_root_password" {
  description = "Keycloak root user password"
  type        = string
}

variable "overrides" {
  # https://github.com/codecentric/helm-charts/blob/master/charts/keycloak/values.yaml
  description = "Keycloak helm chart overrides"
  type        = list(string)
}

variable "node_group" {
  description = "Node key value pair for bound general resources"
  type = object({
    key   = string
    value = string
  })
}
