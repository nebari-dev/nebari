
locals {
{% if cookiecutter.provider == "local" %}
  cluster = {
      certificate_authority = "~/.minikube/ca.crt",
      server = "192.168.49.2:8443"
      name = "minikube"
    }
  context = {
      cluster_name = "minikube",
      user = "minikube",
      namespace = "default"
{% if cookiecutter.local.kube_context is defined %}
      name = "{{ cookiecutter.local.kube_context }}"
{% else %}
      name = "minikube"
{% endif %}
    }
  user = {
      name = "minikube",
      client_certificate = "~/.minikube/profiles/minikube/client.crt",
      client_key = "~/.minikube/profiles/minikube/client.key"
    }
{% elif cookiecutter.provider == "azure" %}
  cluster = {
      certificate_authority_data = module.kubernetes.credentials.cluster_ca_certificate,
      server = module.kubernetes.credentials.endpoint
      name = local.cluster_name
    }
  context = {
      cluster_name = local.cluster_name,
      user = local.cluster_name,
      name = local.cluster_name,
  }
  user = {
      name = module.kubernetes.credentials.username,
      password = module.kubernetes.credentials.password,
      client_certificate = module.kubernetes.credentials.client_certificate,
      client_key = module.kubernetes.credentials.client_key
    }
{% else %}
  cluster = {
      certificate_authority_data = module.kubernetes.credentials.cluster_ca_certificate,
      server = module.kubernetes.credentials.endpoint
      name = local.cluster_name
    }
  context = {
      cluster_name = local.cluster_name,
      user = local.cluster_name,
      name = local.cluster_name,
  }
  user = {
      token = module.kubernetes.credentials.token
    }
{% endif %}
{% if cookiecutter.provider == "aws" %}
  exec {
    api_version = "client.authentication.k8s.io/v1alpha1"
    args        = ["eks", "get-token", "--cluster-name", local.cluster_name]
    command     = "aws"
  }
{% endif %}
}

resource "local_file" "kubeconfig" {
  content  = "${data.template_file.kubeconfig.rendered}"
  filename = "${path.module}./test.tf"
}

data "template_file" "kubeconfig" {
  #./templates/kubeconfig.tpl
  template = replace(yamlencode(
    {
   "apiVersion" : "v1",
   "clusters" : [
     {
       "cluster" : {
        "certificate-authority": "${local.cluster.certificate_authority}"
        "server": "${local.cluster.server}"
       },
       "name" : "${local.cluster.name}"
     }
   ],
   "contexts" : [
     {
       "context" : {
        "cluster": "${local.context.cluster_name}"
        "namespace": "${local.context.namespace}"
        "user": "${local.context.user}"
       },
       "name" : "${local.context.name}"
     }
   ],
   "current-context" : ""
   "kind" : "Config",
   "preferences": "{}",
   "users" : [
     {
       "name" : "${local.user.name}",
       "user" : {
        "client-certificate": "${local.user.client_certificate}"
        "client-key": "${local.user.client_key}"
       }
     }
   ]
}
  ), "\"", "")
  }