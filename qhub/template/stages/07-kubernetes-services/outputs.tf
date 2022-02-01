output "service_urls" {
  description = "service urls for configured services"
  value = {
    conda_store  = {
      url = "https://${var.endpoint}/conda-store/"
      health_url ="https://${var.endpoint}/conda-store/api/v1/"
    }
    dask_gateway = {
      url = "https://${var.endpoint}/gateway/"
      health_url = "https://${var.endpoint}/gateway/api/version"
    }
    jupyterhub   = {
      url = "https://${var.endpoint}/"
      health_url = "https://${var.endpoint}/hub/api/"
    }
    monitoring   = {
      url = "https://${var.endpoint}/monitoring/"
      health_url = "https://${var.endpoint}/monitoring/api/health"
    }
    keycloak     = {
      url = "https://${var.endpoint}/auth/"
      health_url = "https://${var.endpoint}/auth/realms/master"
    }
  }
}
