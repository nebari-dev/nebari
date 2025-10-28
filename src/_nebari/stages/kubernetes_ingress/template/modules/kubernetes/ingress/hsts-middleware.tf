# HSTS (HTTP Strict Transport Security) Middleware
#
# Recovery: If HSTS causes issues, set max_age: 0 and redeploy. Users visit
# the site once over HTTPS and their browsers will immediately clear the policy.
#
resource "kubernetes_manifest" "hsts_middleware" {
  count = var.hsts-enabled ? 1 : 0

  manifest = {
    apiVersion = "traefik.containo.us/v1alpha1"
    kind       = "Middleware"
    metadata = {
      name      = "${var.name}-hsts"
      namespace = var.namespace
    }
    spec = {
      headers = {
        stsSeconds           = var.hsts-max-age
        stsIncludeSubdomains = var.hsts-include-subdomains
        stsPreload           = var.hsts-preload
        forceSTSheader       = true
      }
    }
  }
}
