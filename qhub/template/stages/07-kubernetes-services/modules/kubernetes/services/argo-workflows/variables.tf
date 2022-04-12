variable "namespace" {
  description = "deploy argo server on this namespace"
  type        = string
  default     = "dev"
}

variable "argo-workflows-namespace" {
  description = "deploy argo workflows on this namespace"
  type        = string
  default     = "dev"
}

# variable "node-group" {
#   description = "Node key value pair for bound resources"
#   type = object({
#     key   = string
#     value = string
#   })
# }

variable "external-url" {
  description = "External url that jupyterhub cluster is accessible"
  type        = string
}


variable "overrides" {
  description = "Grafana helm chart overrides"
  type        = list(string)
  default     = []
}
