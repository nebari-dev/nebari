{% if cookiecutter.provider != "kind" -%}
output "ingress_jupyter" {
  description = "jupyter.<domain> ingress endpoint"
  value       = module.kubernetes-ingress.endpoint
}
{% endif -%}
