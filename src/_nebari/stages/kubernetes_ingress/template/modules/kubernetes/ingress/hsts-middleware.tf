# HSTS (HTTP Strict Transport Security) Middleware
#
# The default max-age is 300 seconds (5 minutes) for safe initial deployments.
# After validating that HSTS works correctly with your deployment, increase
# max_age to a production value (e.g., 31536000 = 1 year) in nebari-config.yaml:
#
#   ingress:
#     hsts:
#       enabled: true
#       max_age: 31536000  # 1 year for production
#       include_subdomains: true
#       preload: false
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
