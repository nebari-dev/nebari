variable "namespace" {
  description = "deploy rook-ceph operator in this namespace"
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
}

variable "node_group" {
  description = "Node key value pair for bound resources"
  type = object({
    key   = string
    value = string
  })
}

# variable "argo-workflows-namespace" {
#   description = "deploy argo workflows on this namespace"
#   type        = string
#   default     = "dev"
# }

# variable "node-group" {
#   description = "Node key value pair for bound resources"
#   type = object({
#     key   = string
#     value = string
#   })
# }

# variable "external-url" {
#   description = "External url where jupyterhub cluster is accessible"
#   type        = string
# }

# variable "realm_id" {
#   description = "Keycloak realm to use for deploying openid client"
#   type        = string
# }

# variable "keycloak-read-only-user-credentials" {
#   sensitive   = true
#   description = "Keycloak password for nebari-bot"
#   type        = map(string)
#   default     = {}
# }

# variable "workflow-controller-image-tag" {
#   description = "Image tag for nebari-workflow-controller"
#   type        = string
# }

# variable "nebari-workflow-controller" {
#   description = "Nebari Workflow Controller enabled"
#   type        = bool
# }
