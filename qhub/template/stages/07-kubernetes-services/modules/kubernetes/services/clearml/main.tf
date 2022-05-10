resource "helm_release" "clearml" {
  name              = "clearml"
  namespace         = var.namespace
  chart             = "${path.module}/chart"
  dependency_update = true
  values = concat([
    file("${path.module}/chart/values.yaml")
  ], var.overrides)

  dynamic "set" {
    for_each = var.node_selector
    content {
      name  = "apiserver.nodeSelector.${set.key}"
      value = set.value
    }
  }

  dynamic "set" {
    for_each = var.node_selector
    content {
      name  = "fileserver.nodeSelector.${set.key}"
      value = set.value
    }
  }

  dynamic "set" {
    for_each = var.node_selector
    content {
      name  = "webserver.nodeSelector.${set.key}"
      value = set.value
    }
  }

  dynamic "set" {
    for_each = var.node_selector
    content {
      name  = "agentservices.nodeSelector.${set.key}"
      value = set.value
    }
  }

  //  dynamic "set" {
  //    for_each = var.node_selector
  //    content {
  //      name = "agentGroups.nodeSelector.${set.key}"
  //      value = set.value
  //    }
  //  }

  dynamic "set" {
    for_each = var.node_selector
    content {
      name  = "elasticsearch.nodeSelector.${set.key}"
      value = set.value
    }
  }

}
