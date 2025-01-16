variable "location" {
  # https://cloud.google.com/artifact-registry/docs/docker/pushing-and-pulling
  description = "Location of registry"
  type        = string
}

variable "format" {
  # https://cloud.google.com/artifact-registry/docs/reference/rest/v1/projects.locations.repositories#Format
  description = "The format of packages that are stored in the repository"
  type        = string
  default     = "DOCKER"
}

variable "repository_id" {
  description = "Name of repository"
  type        = string
}
