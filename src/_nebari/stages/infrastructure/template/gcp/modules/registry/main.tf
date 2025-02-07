resource "google_artifact_registry_repository" "registry" {
  # https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/artifact_registry_repository#argument-reference
  repository_id = var.repository_id
  location      = var.location
  format        = var.format
}
