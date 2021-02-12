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
{% endif %}
    }
  }
}
