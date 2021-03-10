{% if cookiecutter.provider != "kind" -%}
output "ingress_jupyter" {
  description = "<domain> ingress endpoint"
  value       = module.kubernetes-ingress.endpoint
}
{% endif -%}
