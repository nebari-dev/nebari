output "service_urls" {
  description = "service urls for configured services"
  value = {
    argo-workflows = {
      url        = var.argo-workflows-enabled ? "https://${var.endpoint}/argo/" : null
      health_url = var.argo-workflows-enabled ? "https://${var.endpoint}/argo/" : null
    }
    conda_store = {
      url        = "https://${var.endpoint}/conda-store/"
      health_url = "https://${var.endpoint}/conda-store/api/v1/"
    }
    dask_gateway = {
      url        = "https://${var.endpoint}/gateway/"
      health_url = "https://${var.endpoint}/gateway/api/version"
    }
    jupyterhub = {
      url        = "https://${var.endpoint}/"
      health_url = "https://${var.endpoint}/hub/api/"
    }
    keycloak = {
      url        = "https://${var.endpoint}/auth/"
      health_url = "https://${var.endpoint}/auth/realms/master"
    }
    monitoring = {
      url        = var.monitoring-enabled ? "https://${var.endpoint}/monitoring/" : null
      health_url = var.monitoring-enabled ? "https://${var.endpoint}/monitoring/api/health" : null
    }
  }
}
