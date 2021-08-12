locals {
{% if cookiecutter.provider == "gcp" %}
  kubeconfig_cluster_name = "gke_{{ cookiecutter.google_cloud_platform.project }}_${var.region}_${local.cluster_name}"
{% endif %}
}
locals {
{% if cookiecutter.provider == "gcp" %}
  kubeconfig_current_context = local.kubeconfig_cluster_name

  kubeconfig_clusters = {
    cluster = {
      certificate-authority-data = module.kubernetes.credentials.cluster_ca
      server                     = module.kubernetes.credentials.endpoint
    },
    name = local.kubeconfig_cluster_name
  }

  kubeconfig_contexts = {
    context = {
      cluster = local.kubeconfig_cluster_name
      user    = local.kubeconfig_cluster_name
    },
    name = local.kubeconfig_cluster_name
  }

  kubeconfig_users = {
    name = local.kubeconfig_cluster_name,
    user = {
      token = module.kubernetes.credentials.token
    }
  }
{% endif %}
}

# Kubeconfig
variable "kubeconfig_path" {
  # This should receive the TF_VAR_kubeconfig_path value
  type    = string
  default = "./QHUB_KUBECONFIG"
}

resource "local_file" "kubeconfig" {
  content = replace(yamlencode({
    "apiVersion" : "v1",
    "kind" : "Config",
    "preferences" : "{}",
    "current-context" : local.kubeconfig_current_context,
    "clusters" : [
      local.kubeconfig_clusters
    ],
    "contexts" : [
      local.kubeconfig_contexts
    ],
    "users" : [
      local.kubeconfig_users
    ]
  }), "\"", "")
  filename = var.kubeconfig_path
}