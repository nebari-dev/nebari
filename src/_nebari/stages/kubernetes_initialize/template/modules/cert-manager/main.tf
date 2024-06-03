resource "helm_release" "cert-manager" {
  name       = "cert-manager"
  namespace  = var.namespace
  repository = "https://charts.jetstack.io"
  chart      = "cert-manager"
  version    = "v1.14.5"
  set {
    name  = "installCRDs"
    value = "true"
  }
}
