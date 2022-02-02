from typing import Dict

from qhub.provider.terraform import TerraformBackend, Provider


def QHubAWSProvider(qhub_config: Dict):
    return Provider("aws", region=qhub_config["amazon_web_services"]["region"])


def QHubGCPProvider(qhub_config: Dict):
    return Provider(
        "google",
        project=qhub_config["google_cloud_platform"]["project"],
        region=qhub_config["google_cloud_platform"]["region"],
    )


def QHubAzureProvider(qhub_config: Dict):
    return Provider("azurerm", features={})


def QHubDigitalOceanProvider(qhub_config: Dict):
    return Provider("digitalocean")


def QHubKubernetesProvider(qhub_config: Dict):
    optional_kwargs = {}
    if qhub_config["provider"] == "aws":
        optional_kwargs["exec"] = {
            "api_version": "client.authentication.k8s.io/v1alpha1",
            "args": [
                "eks",
                "get-token",
                "--cluster-name",
                f"{qhub_config['project_name']}-{qhub_config['namespace']}",
            ],
            "command": "aws",
        }

    return Provider(
        "kubernetes", experiments={"manifest_resource": True}, **optional_kwargs
    )


def QHubTerraformState(directory: str, qhub_config: Dict):
    if qhub_config["terraform_state"]["type"] == "local":
        return {}
    elif qhub_config["terraform_state"]["type"] == "existing":
        return TerraformBackend(
            qhub_config["terraform_state"]["backend"],
            **qhub_config["terraform_state"]["config"],
        )
    elif qhub_config["provider"] == "aws":
        return TerraformBackend(
            "s3",
            bucket=f"{qhub_config['project_name']}-{qhub_config['namespace']}-terraform-state",
            key=f"terraform/{qhub_config['project_name']}-{qhub_config['namespace']}/{directory}.tfstate",
            region=qhub_config["amazon_web_services"]["region"],
            encrypt=True,
            dynamodb_table=f"{qhub_config['project_name']}-{qhub_config['namespace']}-terraform-state-lock",
        )
    elif qhub_config["provider"] == "gcp":
        return TerraformBackend(
            "gcs",
            bucket=f"{qhub_config['project_name']}-{qhub_config['namespace']}-terraform-state",
            prefix=f"terraform/{qhub_config['project_name']}/{directory}",
        )
    elif qhub_config["provider"] == "do":
        return TerraformBackend(
            "s3",
            endpoint=f"{qhub_config['digital_ocean']['region']}.digitaloceanspaces.com",
            region="us-west-1",  # fake aws region required by terraform
            bucket=f"{qhub_config['project_name']}-{qhub_config['namespace']}-terraform-state",
            key=f"terraform/{qhub_config['project_name']}-{qhub_config['namespace']}/{directory}.tfstate",
            skip_credentials_validation=True,
            skip_metadata_api_check=True,
        )
    elif qhub_config["provider"] == "azure":
        return TerraformBackend(
            "azurerm",
            resource_group_name=f"{qhub_config['project_name']}-{qhub_config['namespace']}",
            # storage account must be globally unique
            storage_account_name=f"{qhub_config['project_name']}{qhub_config['namespace']}{qhub_config['azure']['storage_account_postfix']}",
            container_name=f"{qhub_config['project_name']}-{qhub_config['namespace']}state",
            key=f"terraform/{qhub_config['project_name']}-{qhub_config['namespace']}/{directory}",
        )
    elif qhub_config["provider"] == "local":
        optional_kwargs = {}
        if "kube_context" in qhub_config["local"]:
            optional_kwargs["confix_context"] = qhub_config["local"]["kube_context"]
        return TerraformBackend(
            "kubernetes",
            secret_suffix=f"{qhub_config['project_name']}-{qhub_config['namespace']}-{directory}",
            load_config_file=True,
            **optional_kwargs,
        )
    else:
        raise NotImplementedError("state not implemented")
