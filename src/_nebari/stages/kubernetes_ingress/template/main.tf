module "cert_manager" {
  source      = "./modules/cert-manager"
  acme-email  = var.acme-email
  acme-server = var.acme-server
#
#  cluster_issuer_email = "admin@nebari.com"
#  cluster_issuer_name  = "cert-manager-global"
#
#  cluster_issuer_private_key_secret_name = "cert-manager-private-key"
}



module "kubernetes-ingress" {
  source = "./modules/kubernetes/ingress"

  namespace = var.environment

  node-group = var.node_groups.general

  traefik-image = var.traefik-image

  certificate-service       = var.certificate-service
  acme-email                = var.acme-email
  acme-server               = var.acme-server
  certificate-secret-name   = var.certificate-secret-name
  load-balancer-annotations = var.load-balancer-annotations
#  load-balancer-annotations = {
#    "cert-manager.io/cluster-issuer" = "cert-manager-global"
#  }
  load-balancer-ip          = var.load-balancer-ip
  additional-arguments      = var.additional-arguments
}
