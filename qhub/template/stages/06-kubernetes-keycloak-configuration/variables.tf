variable "realm" {
  description = "Keycloak realm to use for QHub"
  type        = string
}

variable "keycloak_groups" {
  description = "Permission groups in keycloak used for granting access to services"
  type = set(string)
  default = ["admin", "developer", "practitioner", "viewer", "projects"]
}

variable "authentication" {
  description = "Authentication configuration for keycloak"
  type = object({
    type = string
    config = map(string)
  })
  default = {
    config = {}
    type = ""
  }
}
