module "kubernetes-jupyterhub-ssh" {
  source = "./modules/kubernetes/services/jupyterhub-ssh"

  namespace          = var.environment
  jupyterhub_api_url = module.jupyterhub.internal_jupyterhub_url

  node-group              = var.node_groups.general
  persistent_volume_claim = module.jupyterhub-nfs-mount.persistent_volume_claim.name
}
