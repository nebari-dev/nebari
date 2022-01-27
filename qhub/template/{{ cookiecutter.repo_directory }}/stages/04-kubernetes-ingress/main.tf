module "kubernetes-ingress" {
  source = "./modules/kubernetes/ingress"

  namespace = var.environment

  node-group = var.node_groups.general

  enable-certificates     = var.enable-certificates
  acme-email              = var.acme-email
  acme-server             = var.acme-server
  certificate-secret-name = var.certificate-secret-name
}
