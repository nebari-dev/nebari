module "helm-extension" {
  for_each = { for extension in var.helm_extensions : extension.name => extension }

  source        = "./modules/helm-extensions"
  name          = each.value.name
  namespace     = var.environment
  repository    = each.value.repository
  chart         = each.value.chart
  chart_version = each.value.version
  overrides     = lookup(each.value, "overrides", {})
}
