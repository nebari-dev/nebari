from _nebari.provider.terraform import Data, Provider, Resource, TerraformBackend
from _nebari.utils import (
    AZURE_TF_STATE_RESOURCE_GROUP_SUFFIX,
    construct_azure_resource_group_name,
    deep_merge,
)
from nebari import schema


def NebariKubernetesProvider(nebari_config: schema.Main):
    if nebari_config.provider == "aws":
        cluster_name = f"{nebari_config.escaped_project_name}-{nebari_config.namespace}"
        # The AWS provider needs to be added, as we are using aws related resources #1254
        return deep_merge(
            Data("aws_eks_cluster", "default", name=cluster_name),
            Data("aws_eks_cluster_auth", "default", name=cluster_name),
            Provider("aws", region=nebari_config.amazon_web_services.region),
            Provider(
                "kubernetes",
                host="${data.aws_eks_cluster.default.endpoint}",
                cluster_ca_certificate="${base64decode(data.aws_eks_cluster.default.certificate_authority[0].data)}",
                token="${data.aws_eks_cluster_auth.default.token}",
            ),
        )
    return Provider(
        "kubernetes",
    )


def NebariHelmProvider(nebari_config: schema.Main):
    if nebari_config.provider == "aws":
        cluster_name = f"{nebari_config.escaped_project_name}-{nebari_config.namespace}"

        return deep_merge(
            Data("aws_eks_cluster", "default", name=cluster_name),
            Data("aws_eks_cluster_auth", "default", name=cluster_name),
            Provider(
                "helm",
                kubernetes=dict(
                    host="${data.aws_eks_cluster.default.endpoint}",
                    cluster_ca_certificate="${base64decode(data.aws_eks_cluster.default.certificate_authority[0].data)}",
                    token="${data.aws_eks_cluster_auth.default.token}",
                ),
            ),
        )
    return Provider("helm")


def NebariTerraformState(directory: str, nebari_config: schema.Main):
    if nebari_config.terraform_state.type == "local":
        return {}
    elif nebari_config.terraform_state.type == "existing":
        return TerraformBackend(
            nebari_config["terraform_state"]["backend"],
            **nebari_config["terraform_state"]["config"],
        )
    elif nebari_config.provider == "aws":
        return TerraformBackend(
            "s3",
            bucket=f"{nebari_config.escaped_project_name}-{nebari_config.namespace}-terraform-state",
            key=f"terraform/{nebari_config.escaped_project_name}-{nebari_config.namespace}/{directory}.tfstate",
            region=nebari_config.amazon_web_services.region,
            encrypt=True,
            dynamodb_table=f"{nebari_config.escaped_project_name}-{nebari_config.namespace}-terraform-state-lock",
        )
    elif nebari_config.provider == "gcp":
        return TerraformBackend(
            "gcs",
            bucket=f"{nebari_config.escaped_project_name}-{nebari_config.namespace}-terraform-state",
            prefix=f"terraform/{nebari_config.escaped_project_name}/{directory}",
        )
    elif nebari_config.provider == "do":
        return TerraformBackend(
            "s3",
            endpoint=f"{nebari_config.digital_ocean.region}.digitaloceanspaces.com",
            region="us-west-1",  # fake aws region required by terraform
            bucket=f"{nebari_config.escaped_project_name}-{nebari_config.namespace}-terraform-state",
            key=f"terraform/{nebari_config.escaped_project_name}-{nebari_config.namespace}/{directory}.tfstate",
            skip_credentials_validation=True,
            skip_metadata_api_check=True,
        )
    elif nebari_config.provider == "azure":
        return TerraformBackend(
            "azurerm",
            resource_group_name=construct_azure_resource_group_name(
                project_name=nebari_config.project_name,
                namespace=nebari_config.namespace,
                base_resource_group_name=nebari_config.azure.resource_group_name,
                suffix=AZURE_TF_STATE_RESOURCE_GROUP_SUFFIX,
            ),
            # storage account must be globally unique
            storage_account_name=f"{nebari_config.escaped_project_name}{nebari_config.namespace}{nebari_config.azure.storage_account_postfix}",
            container_name=f"{nebari_config.escaped_project_name}-{nebari_config.namespace}-state",
            key=f"terraform/{nebari_config.escaped_project_name}-{nebari_config.namespace}/{directory}",
        )
    elif nebari_config.provider == "existing":
        optional_kwargs = {}
        if "kube_context" in nebari_config.existing:
            optional_kwargs["config_context"] = nebari_config.existing.kube_context
        return TerraformBackend(
            "kubernetes",
            secret_suffix=f"{nebari_config.escaped_project_name}-{nebari_config.namespace}-{directory}",
            load_config_file=True,
            **optional_kwargs,
        )
    elif nebari_config.provider == "local":
        optional_kwargs = {}
        if "kube_context" in nebari_config.local:
            optional_kwargs["config_context"] = nebari_config.local.kube_context
        return TerraformBackend(
            "kubernetes",
            secret_suffix=f"{nebari_config.escaped_project_name}-{nebari_config.namespace}-{directory}",
            load_config_file=True,
            **optional_kwargs,
        )
    else:
        raise NotImplementedError("state not implemented")


def NebariConfig(nebari_config: schema.Main):
    return Resource("terraform_data", "nebari_config", input=nebari_config.model_dump())
