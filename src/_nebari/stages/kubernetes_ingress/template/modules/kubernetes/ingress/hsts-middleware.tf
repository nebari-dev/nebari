# HSTS (HTTP Strict Transport Security) Middleware
#
# Important: The default max-age is set to 30 seconds for initial testing.
# After validating that HSTS works correctly with your deployment, you should
# increase max_age to a production value (e.g., 31536000 = 1 year) in your
# nebari-config.yaml:
#
#   ingress:
#     hsts:
#       enabled: true
#       max_age: 31536000  # 1 year
#       include_subdomains: true
#       preload: false
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
        stsSeconds             = var.hsts-max-age
        stsIncludeSubdomains   = var.hsts-include-subdomains
        stsPreload             = var.hsts-preload
        forceSTSHeader         = true
      }
    }
  }
}
