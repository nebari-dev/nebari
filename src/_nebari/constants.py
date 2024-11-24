CURRENT_RELEASE = "2024.11.1"

HELM_VERSION = "v3.15.3"
KUSTOMIZE_VERSION = "5.4.3"
OPENTOFU_VERSION = "1.8.3"

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
AZURE_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-azure"
AWS_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-aws"
GCP_ENV_DOCS = "https://www.nebari.dev/docs/how-tos/nebari-gcp"

# DEFAULT CLOUD REGIONS
AWS_DEFAULT_REGION = "us-east-1"
AZURE_DEFAULT_REGION = "Central US"
GCP_DEFAULT_REGION = "us-central1"

# TERRAFORM REQUIRED PROVIDERS
REQUIRED_PROVIDERS = {
    "aws": {
        "_name": "aws",
        "source": "hashicorp/aws",
        "version": "5.12.0",
    },
    "azurerm": {
        "_name": "azurerm",
        "source": "hashicorp/azurerm",
        "version": "=3.97.1",
    },
    "docker": {
        "_name": "docker",
        "source": "kreuzwerker/docker",
        "version": "2.16.0",
    },
    "google": {
        "_name": "google",
        "source": "hashicorp/google",
        "version": "4.83.0",
    },
    "helm": {
        "_name": "helm",
        "source": "hashicorp/kubernetes",
        "version": "2.1.2",
    },
    "keycloak": {
        "_name": "keycloak",
        "source": "mrparkers/keycloak",
        "version": "3.7.0",
    },
    "kind": {
        "_name": "kind",
        "source": "registry.terraform.io/tehcyx/kind",
        "version": "0.4.0",
    },
    "kubectl": {
        "_name": "kubectl",
        "source": "gavinbunney/kubectl",
        "version": ">= 1.7.0",
    },
    "kubernetes": {
        "_name": "kubernetes",
        "source": "hashicorp/kubernetes",
        "version": ">= 2.20.0",
    },
}
