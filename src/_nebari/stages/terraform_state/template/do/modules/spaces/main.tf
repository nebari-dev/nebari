resource "digitalocean_spaces_bucket" "main" {
  name   = var.name
  region = var.region

  force_destroy = var.force_destroy

  acl = (var.public ? "public-read" : "private")
}
