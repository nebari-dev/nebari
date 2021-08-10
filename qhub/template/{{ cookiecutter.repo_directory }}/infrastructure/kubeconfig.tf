
locals {
# {% if cookiecutter.provider == "local" %}
#   cluster = {
#       certificate_authority = "~/.minikube/ca.crt",
#       server = "192.168.49.2:8443"
#       name = "minikube"
#     }
#   context = {
#       cluster_name = "minikube",
#       user = "minikube",
#       namespace = "default"
# {% if cookiecutter.local.kube_context is defined %}
#       name = "{{ cookiecutter.local.kube_context }}"
# {% else %}
#       name = "minikube"
# {% endif %}
#     }
#   user = {
#       name = "minikube",
#       client_certificate = "~/.minikube/profiles/minikube/client.crt",
#       client_key = "~/.minikube/profiles/minikube/client.key"
#     }
# {% elif cookiecutter.provider == "azure" %}
#   cluster = {
#       certificate_authority_data = module.kubernetes.credentials.cluster_ca_certificate,
#       server = module.kubernetes.credentials.endpoint
#       name = local.cluster_name
#     }
#   context = {
#       cluster_name = local.cluster_name,
#       user = local.cluster_name,
#       name = local.cluster_name,
#   }
#   user = {
#       name = module.kubernetes.credentials.username,
#       password = module.kubernetes.credentials.password,
#       client_certificate = module.kubernetes.credentials.client_certificate,
#       client_key = module.kubernetes.credentials.client_key
#     }
# {% else %}
#   cluster = {
#       certificate_authority_data = module.kubernetes.credentials.cluster_ca_certificate,
#       server = module.kubernetes.credentials.endpoint
#       name = local.cluster_name
#     }
#   context = {
#       cluster_name = local.cluster_name,
#       user = local.cluster_name,
#       name = local.cluster_name,
#   }
#   user = {
#       token = module.kubernetes.credentials.token
#     }
# {% endif %}
# {% if cookiecutter.provider == "aws" %}
#   exec {
#     api_version = "client.authentication.k8s.io/v1alpha1"
#     args        = ["eks", "get-token", "--cluster-name", local.cluster_name]
#     command     = "aws"
#   }
# {% endif %}
  cluster = {
{% if cookiecutter.provider == "local" %}
    certificate_authority = "~/.minikube/ca.crt",
    server = "192.168.49.2:8443"
    name = "minikube"
{% else %}
    certificate_authority_data = "",
    server = ""
    name = ""
{% endif %}
  }
  context = {
{% if cookiecutter.provider == "local" %}
    cluster_name = "minikube",
    user = "minikube",
    namespace = "default"
{% else %}
    cluster_name = local.cluster_name,
    user = local.cluster_name,
    name = local.cluster_name,
{% endif %}
  }
  user = {
{% if cookiecutter.provider == "local" %}
    name = "minikube",
    client_certificate = "~/.minikube/profiles/minikube/client.crt",
    client_key = "~/.minikube/profiles/minikube/client.key"
{% else %}
    token = module.kubernetes.credentials.token
{% endif %}
  }
{% if cookiecutter.local.kube_context is defined %}
  current_context = "{{ cookiecutter.local.kube_context }}"
{% else %}
  current_context = ""
{% endif %}
  }
}

resource "local_file" "kubeconfig" {
  content  = "${data.template_file.kubeconfig.rendered}"
  filename = "${path.module}./test.tf"
}

data "template_file" "kubeconfig" {
  template = "${file("kubeconfig.tpl")}"
  vars = {
    contexts = local.contexts,
    clusters = local.clusters,
    users = local.users,
    current_context = local.current_context
  }
}