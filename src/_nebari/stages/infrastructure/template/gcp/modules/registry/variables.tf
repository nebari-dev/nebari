variable "location" {
  # https://cloud.google.com/container-registry/docs/pushing-and-pulling#pushing_an_image_to_a_registry
  description = "Location of registry"
  type        = string
  default     = "US"
}
