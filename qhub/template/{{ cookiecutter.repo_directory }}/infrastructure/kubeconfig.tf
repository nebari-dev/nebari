
locals {
  cluster = {
{% if cookiecutter.provider == "local" %}
      certificate_authority_data = "~/.minikube/ca.crt",
      server = "$(minikube ip):8443"
      name = "minikube"
{% endif %}
    }
{% if cookiecutter.local.kube_context is defined %}
  context = "{{ cookiecutter.local.kube_context }}"
{% else %}
  context = {
      cluster_name = "",
      user = "",
      name = ""
    }
{% endif %}
  user = {
{% if cookiecutter.provider == "local" %}
      name = "minikube",
      client_certificate = "~/.minikube/profiles/minikube/client.crt",
      client_key = "~/.minikube/profiles/minikube/client.key"
{% endif %}
    }
}

resource "local_file" "kubeconfig" {
  content  = "${data.template_file.kubeconfig.rendered}"
  filename = "${path.module}./test.tf"
  depends_on = [
    module.kubernetes
  ]
}

data "template_file" "kubeconfig" {
  #./templates/kubeconfig.tpl
  template = yamlencode(
    {
   "apiVersion" : "v1",
   "clusters" : [
     {
       "cluster" : {
         "certificate-authority-data": "${local.cluster.certificate_authority_data}",
         "server": "${local.cluster.server}"
       },
       "name" : "${local.cluster.name}"
     }
   ],
   "contexts" : [
     {
       "context" : {
         "cluster": "${local.context.cluster_name}",
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
       "name" : "",
       "user" : {
        "client_certificate": "${local.user.client_certificate}",
        "client-key": "${local.user.client_key}"
       }
     }
   ]
}
  )
  }