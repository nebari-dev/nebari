provider "kubernetes" {
  experiments {
    manifest_resource = true
  }
{% if cookiecutter.provider == "aws" %}
  exec {
    api_version = "client.authentication.k8s.io/v1alpha1"
    args        = ["eks", "get-token", "--cluster-name", local.cluster_name]
    command     = "aws"
  }
{% endif %}
}


provider "helm" {

}
