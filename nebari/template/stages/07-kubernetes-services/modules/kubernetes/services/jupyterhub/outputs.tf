output "internal_jupyterhub_url" {
  description = "internal url for jupyterhub"
  value       = "http://proxy-public.${var.namespace}:80"
}


output "services" {
  description = "Jupyterhub registered services"
  value = {
    for service in var.services : service => {
      name      = service
      api_token = random_password.service_token[service].result
    }
  }
}
