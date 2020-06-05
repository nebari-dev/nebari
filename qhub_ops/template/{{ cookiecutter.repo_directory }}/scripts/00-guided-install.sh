#!/usr/bin/env bash
set -euo pipefail

# 01 Check configuration exists
if [ ! -f qhub-ops-config.yaml ]; then
   echo "ERROR: configuration file \"qhub-ops-config.yaml\" does not exist"
   exit 1
fi

# 02 Check available commands
if [ ! -f "$(command -v terraform)" ]; then
    echo "ERROR: terraform command is not installed"
    exit 1
fi

# 03 Check Environment Variables
{% if cookiecutter.provider == 'gcp' %}
if [[ -z "${GOOGLE_CREDENTIALS}" ]] || [[ -z "${PROJECT_ID}" ]]; then
    echo "Environment variables required for GCP (GOOGLE_CREDENTIALS, PROJECT_ID) must be set"
fi
{% elif cookiecutter.provider == 'aws' %}
if [[ -z "${AWS_ACCESS_KEY_ID}" ]] || [[ -z "${AWS_SECRET_ACCESS_KEY}" ]] || [[ -z "${AWS_DEFAULT_REGION}" ]]; then
    echo "Environment variables required for AWS (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION) must be set"
fi
{% elif cookiecutter.provider == 'do' %}
if [[ -z "${AWS_ACCESS_KEY_ID}" ]] || [[ -z "${AWS_SECRET_ACCESS_KEY}" ]] || [[ -z "${SPACES_ACCESS_KEY_ID}" ]] || [[ -z "${SPACES_SECRET_ACCESS_KEY}" ]] || [[ -z "${DIGITALOCEAN_TOKEN}" ]]; then
    echo "Environment variables required for DO (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, SPACES_ACCESS_KEY_ID, SPACES_SECRET_ACCESS_KEY, DIGITALOCEAN_TOKEN) must be set"
fi
{% endif %}

# 04 Check that oauth settings are set
read -s -p "Ensure that oauth settings are in configuration [Press Enter]"

# 05 Create terraform backend remote state bucket
cd terraform-state
terraform init
terraform apply -auto-approve

# 06 Create qhub initial state
cd ../infrastructure
terraform init
terraform apply -auto-approve -target=module.kubernetes -target=module.kubernetes-initialization -target=module.kubernetes-ingress

# 07 Update DNS to point to qhub deployment
read -s -p "Take IP Address Above and update DNS to point to \"jupyter.{{ cookiecutter.endpoint }}\" [Press Enter when Complete]"

terraform apply -auto-approve
