
from _nebari.provider.terraform import Data, Provider, TerraformBackend
from _nebari.utils import deep_merge
from nebari import schema


def NebariAWSProvider(nebari_config: schema.Main):
    return Provider("aws", region=nebari_config.amazon_web_services.region)


def NebariGCPProvider(nebari_config: schema.Main):
    return Provider(
        "google",
        project=nebari_config.google_cloud_platform.project,
        region=nebari_config.google_cloud_platform.region,
    )


def NebariAzureProvider(nebari_config: schema.Main):
    return Provider("azurerm", features={})


def NebariDigitalOceanProvider(nebari_config: schema.Main):
    return Provider("digitalocean")


def NebariKubernetesProvider(nebari_config: schema.Main):
    if nebari_config.provider == schema.ProviderEnum.aws:
        cluster_name = f"{nebari_config.project_name}-{nebari_config.namespace}"
        # The AWS provider needs to be added, as we are using aws related resources #1254
        return deep_merge(
            Data("aws_eks_cluster", "default", name=cluster_name),
            Data("aws_eks_cluster_auth", "default", name=cluster_name),
            Provider("aws", region=nebari_config.amazon_web_services.region),
            Provider(
                "kubernetes",
                experiments={"manifest_resource": True},
                host="${data.aws_eks_cluster.default.endpoint}",
                cluster_ca_certificate="${base64decode(data.aws_eks_cluster.default.certificate_authority[0].data)}",
                token="${data.aws_eks_cluster_auth.default.token}",
            ),
        )
    return Provider(
        "kubernetes",
        experiments={"manifest_resource": True},
    )


def NebariHelmProvider(nebari_config: schema.Main):
    if nebari_config.provider == schema.ProviderEnum.aws:
        cluster_name = f"{nebari_config.project_name}-{nebari_config.namespace}"

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
    if nebari_config.terraform_state.type == schema.TerraformStateEnum.local:
        return {}
    elif nebari_config.terraform_state.type == schema.TerraformStateEnum.existing:
        return TerraformBackend(
            nebari_config["terraform_state"]["backend"],
            **nebari_config["terraform_state"]["config"],
        )
    elif nebari_config.provider == schema.ProviderEnum.aws:
        return TerraformBackend(
            "s3",
            bucket=f"{nebari_config.project_name}-{nebari_config.namespace}-terraform-state",
            key=f"terraform/{nebari_config.project_name}-{nebari_config.namespace}/{directory}.tfstate",
            region=nebari_config.amazon_web_services.region,
            encrypt=True,
            dynamodb_table=f"{nebari_config.project_name}-{nebari_config.namespace}-terraform-state-lock",
        )
    elif nebari_config.provider == schema.ProviderEnum.gcp:
        return TerraformBackend(
            "gcs",
            bucket=f"{nebari_config.project_name}-{nebari_config.namespace}-terraform-state",
            prefix=f"terraform/{nebari_config.project_name}/{directory}",
        )
    elif nebari_config.provider == schema.ProviderEnum.do:
        return TerraformBackend(
            "s3",
            endpoint=f"{nebari_config.digital_ocean.region}.digitaloceanspaces.com",
            region="us-west-1",  # fake aws region required by terraform
            bucket=f"{nebari_config.project_name}-{nebari_config.namespace}-terraform-state",
            key=f"terraform/{nebari_config.project_name}-{nebari_config.namespace}/{directory}.tfstate",
            skip_credentials_validation=True,
            skip_metadata_api_check=True,
        )
    elif nebari_config.provider == schema.ProviderEnum.azure:
        return TerraformBackend(
            "azurerm",
            resource_group_name=f"{nebari_config.project_name}-{nebari_config.namespace}-state",
            # storage account must be globally unique
            storage_account_name=f"{nebari_config.project_name}{nebari_config.namespace}{nebari_config.azure.storage_account_postfix}",
            container_name=f"{nebari_config.project_name}-{nebari_config.namespace}-state",
            key=f"terraform/{nebari_config.project_name}-{nebari_config.namespace}/{directory}",
        )
    elif nebari_config.provider == schema.ProviderEnum.existing:
        optional_kwargs = {}
        if "kube_context" in nebari_config.existing:
            optional_kwargs["config_context"] = nebari_config.existing.kube_context
        return TerraformBackend(
            "kubernetes",
            secret_suffix=f"{nebari_config.project_name}-{nebari_config.namespace}-{directory}",
            load_config_file=True,
            **optional_kwargs,
        )
    elif nebari_config.provider == schema.ProviderEnum.local:
        optional_kwargs = {}
        if "kube_context" in nebari_config.local:
            optional_kwargs["config_context"] = nebari_config.local.kube_context
        return TerraformBackend(
            "kubernetes",
            secret_suffix=f"{nebari_config.project_name}-{nebari_config.namespace}-{directory}",
            load_config_file=True,
            **optional_kwargs,
        )
    else:
        raise NotImplementedError("state not implemented")
