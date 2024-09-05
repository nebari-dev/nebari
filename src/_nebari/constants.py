CURRENT_RELEASE = "2024.7.1"

HELM_VERSION = "v3.15.3"
KUSTOMIZE_VERSION = "5.4.3"
# NOTE: Terraform cannot be upgraded further due to Hashicorp licensing changes
# implemented in August 2023.
# https://www.hashicorp.com/license-faq
TERRAFORM_VERSION = "1.5.7"

KUBERHEALTHY_HELM_VERSION = "100"

# 04-kubernetes-ingress
DEFAULT_TRAEFIK_IMAGE_TAG = "2.9.1"

HIGHEST_SUPPORTED_K8S_VERSION = ("1", "29", "2")
DEFAULT_GKE_RELEASE_CHANNEL = "UNSPECIFIED"

DEFAULT_NEBARI_DASK_VERSION = CURRENT_RELEASE
DEFAULT_NEBARI_IMAGE_TAG = CURRENT_RELEASE
DEFAULT_NEBARI_WORKFLOW_CONTROLLER_IMAGE_TAG = CURRENT_RELEASE

DEFAULT_CONDA_STORE_IMAGE_TAG = "2024.3.1"

LATEST_SUPPORTED_PYTHON_VERSION = "3.10"


# DOCS
DO_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-do"
AZURE_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-azure"
AWS_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-aws"
GCP_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-gcp"

# DEFAULT CLOUD REGIONS
AWS_DEFAULT_REGION = "us-east-1"
AZURE_DEFAULT_REGION = "Central US"
GCP_DEFAULT_REGION = "us-central1"
DO_DEFAULT_REGION = "nyc3"
