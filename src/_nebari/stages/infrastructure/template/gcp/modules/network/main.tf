resource "google_compute_network" "main" {
  name        = var.name
  description = "VCP Gateway for ${var.name}"
}

data "google_compute_subnetwork" "main" {
  name   = var.name
  region = var.region
}
