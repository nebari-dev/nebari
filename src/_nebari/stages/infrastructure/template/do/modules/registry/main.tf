resource "digitalocean_container_registry" "registry" {
  name                   = var.name
  subscription_tier_slug = "starter"
}
