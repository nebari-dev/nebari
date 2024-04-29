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

# variable "custom_themes_repo" {
#   description = "Custom themes repo for keycloak"
#   type        = string
# }

# variable "custom_themes_branch" {
#   description = "Custom themes branch for keycloak"
#   type        = string

# }

variable "themes" {
  description = "Custom themes configuration for keycloak"
  type = object({
    repo   = string
    branch = string
  })

}
