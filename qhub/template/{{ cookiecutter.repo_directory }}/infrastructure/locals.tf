locals {
  additional_tags = {
    Project     = var.name
    Owner       = "terraform"
    Environment = var.environment
  }

  cluster_name = "${var.name}-${var.environment}"

  node_groups = {
    general = {
{%- if cookiecutter.provider == "aws" %}
      key   = "eks.amazonaws.com/nodegroup"
      value = "general"
{%- elif cookiecutter.provider == "gcp" %}
      key   = "cloud.google.com/gke-nodepool"
      value = "general"
{%- elif cookiecutter.provider == "azure" %}
      key   = "azure-node-pool"
      value = "general"
{%- elif cookiecutter.provider == "do" %}
      key   = "doks.digitalocean.com/node-pool"
      value = "general"
{%- else %}
      key   = "{{ cookiecutter.local.node_selectors.general.key }}"
      value = "{{ cookiecutter.local.node_selectors.general.value }}"
{% endif %}
    }

    user = {
{%- if cookiecutter.provider == "aws" %}
      key   = "eks.amazonaws.com/nodegroup"
      value = "user"
{%- elif cookiecutter.provider == "gcp" %}
      key   = "cloud.google.com/gke-nodepool"
      value = "user"
{%- elif cookiecutter.provider == "azure" %}
      key   = "azure-node-pool"
      value = "user"
{%- elif cookiecutter.provider == "do" %}
      key   = "doks.digitalocean.com/node-pool"
      value = "user"
{%- else %}
      key   = "{{ cookiecutter.local.node_selectors.user.key }}"
      value = "{{ cookiecutter.local.node_selectors.user.value }}"
{% endif %}
    }

    worker = {
{%- if cookiecutter.provider == "aws" %}
      key   = "eks.amazonaws.com/nodegroup"
      value = "worker"
{%- elif cookiecutter.provider == "gcp" %}
      key   = "cloud.google.com/gke-nodepool"
      value = "worker"
{%- elif cookiecutter.provider == "azure" %}
      key   = "azure-node-pool"
      value = "worker"
{%- elif cookiecutter.provider == "do" %}
      key   = "doks.digitalocean.com/node-pool"
      value = "worker"
{%- else %}
      key   = "{{ cookiecutter.local.node_selectors.worker.key }}"
      value = "{{ cookiecutter.local.node_selectors.worker.value }}"
{% endif %}
    }
  }

  forwardauth-jh-client-id      = "forwardauthjupyterhubserviceclient"
  forwardauth-callback-url-path = "/forwardauth/_oauth"
}
