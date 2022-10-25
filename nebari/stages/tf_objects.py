from typing import Dict

from nebari.provider.terraform import (
    Data,
    Provider,
    TerraformBackend,
    tf_render_objects,
)
from nebari.utils import deep_merge


def nebariAWSProvider(nebari_config: Dict):
    return Provider("aws", region=nebari_config["amazon_web_services"]["region"])


def nebariGCPProvider(nebari_config: Dict):
    return Provider(
        "google",
        project=nebari_config["google_cloud_platform"]["project"],
        region=nebari_config["google_cloud_platform"]["region"],
    )


def nebariAzureProvider(nebari_config: Dict):
    return Provider("azurerm", features={})


def nebariDigitalOceanProvider(nebari_config: Dict):
    return Provider("digitalocean")


def nebariKubernetesProvider(nebari_config: Dict):
    if nebari_config["provider"] == "aws":
        cluster_name = f"{nebari_config['project_name']}-{nebari_config['namespace']}"
        # The AWS provider needs to be added, as we are using aws related resources #1254
        return deep_merge(
            Data("aws_eks_cluster", "default", name=cluster_name),
            Data("aws_eks_cluster_auth", "default", name=cluster_name),
            Provider("aws", region=nebari_config["amazon_web_services"]["region"]),
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


def nebariHelmProvider(nebari_config: Dict):
    if nebari_config["provider"] == "aws":
        cluster_name = f"{nebari_config['project_name']}-{nebari_config['namespace']}"

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


def nebariTerraformState(directory: str, nebari_config: Dict):
    if nebari_config["terraform_state"]["type"] == "local":
        return {}
    elif nebari_config["terraform_state"]["type"] == "existing":
        return TerraformBackend(
            nebari_config["terraform_state"]["backend"],
            **nebari_config["terraform_state"]["config"],
        )
    elif nebari_config["provider"] == "aws":
        return TerraformBackend(
            "s3",
            bucket=f"{nebari_config['project_name']}-{nebari_config['namespace']}-terraform-state",
            key=f"terraform/{nebari_config['project_name']}-{nebari_config['namespace']}/{directory}.tfstate",
            region=nebari_config["amazon_web_services"]["region"],
            encrypt=True,
            dynamodb_table=f"{nebari_config['project_name']}-{nebari_config['namespace']}-terraform-state-lock",
        )
    elif nebari_config["provider"] == "gcp":
        return TerraformBackend(
            "gcs",
            bucket=f"{nebari_config['project_name']}-{nebari_config['namespace']}-terraform-state",
            prefix=f"terraform/{nebari_config['project_name']}/{directory}",
        )
    elif nebari_config["provider"] == "do":
        return TerraformBackend(
            "s3",
            endpoint=f"{nebari_config['digital_ocean']['region']}.digitaloceanspaces.com",
            region="us-west-1",  # fake aws region required by terraform
            bucket=f"{nebari_config['project_name']}-{nebari_config['namespace']}-terraform-state",
            key=f"terraform/{nebari_config['project_name']}-{nebari_config['namespace']}/{directory}.tfstate",
            skip_credentials_validation=True,
            skip_metadata_api_check=True,
        )
    elif nebari_config["provider"] == "azure":
        return TerraformBackend(
            "azurerm",
            resource_group_name=f"{nebari_config['project_name']}-{nebari_config['namespace']}-state",
            # storage account must be globally unique
            storage_account_name=f"{nebari_config['project_name']}{nebari_config['namespace']}{nebari_config['azure']['storage_account_postfix']}",
            container_name=f"{nebari_config['project_name']}-{nebari_config['namespace']}-state",
            key=f"terraform/{nebari_config['project_name']}-{nebari_config['namespace']}/{directory}",
        )
    elif nebari_config["provider"] == "existing":
        optional_kwargs = {}
        if "kube_context" in nebari_config["existing"]:
            optional_kwargs["confix_context"] = nebari_config["existing"][
                "kube_context"
            ]
        return TerraformBackend(
            "kubernetes",
            secret_suffix=f"{nebari_config['project_name']}-{nebari_config['namespace']}-{directory}",
            load_config_file=True,
            **optional_kwargs,
        )
    elif nebari_config["provider"] == "local":
        optional_kwargs = {}
        if "kube_context" in nebari_config["local"]:
            optional_kwargs["confix_context"] = nebari_config["local"]["kube_context"]
        return TerraformBackend(
            "kubernetes",
            secret_suffix=f"{nebari_config['project_name']}-{nebari_config['namespace']}-{directory}",
            load_config_file=True,
            **optional_kwargs,
        )
    else:
        raise NotImplementedError("state not implemented")


def stage_01_terraform_state(config):
    if config["provider"] == "gcp":
        return {
            "stages/01-terraform-state/gcp/_nebari.tf.json": tf_render_objects(
                [
                    nebariGCPProvider(config),
                ]
            )
        }
    elif config["provider"] == "aws":
        return {
            "stages/01-terraform-state/aws/_nebari.tf.json": tf_render_objects(
                [
                    nebariAWSProvider(config),
                ]
            )
        }
    else:
        return {}


def stage_02_infrastructure(config):
    if config["provider"] == "gcp":
        return {
            "stages/02-infrastructure/gcp/_nebari.tf.json": tf_render_objects(
                [
                    nebariGCPProvider(config),
                    nebariTerraformState("02-infrastructure", config),
                ]
            )
        }
    elif config["provider"] == "do":
        return {
            "stages/02-infrastructure/do/_nebari.tf.json": tf_render_objects(
                [
                    nebariTerraformState("02-infrastructure", config),
                ]
            )
        }
    elif config["provider"] == "azure":
        return {
            "stages/02-infrastructure/azure/_nebari.tf.json": tf_render_objects(
                [
                    nebariTerraformState("02-infrastructure", config),
                ]
            ),
        }
    elif config["provider"] == "aws":
        return {
            "stages/02-infrastructure/aws/_nebari.tf.json": tf_render_objects(
                [
                    nebariAWSProvider(config),
                    nebariTerraformState("02-infrastructure", config),
                ]
            )
        }
    else:
        return {}


def stage_03_kubernetes_initialize(config):
    return {
        "stages/03-kubernetes-initialize/_nebari.tf.json": tf_render_objects(
            [
                nebariTerraformState("03-kubernetes-initialize", config),
                nebariKubernetesProvider(config),
                nebariHelmProvider(config),
            ]
        ),
    }


def stage_04_kubernetes_ingress(config):
    return {
        "stages/04-kubernetes-ingress/_nebari.tf.json": tf_render_objects(
            [
                nebariTerraformState("04-kubernetes-ingress", config),
                nebariKubernetesProvider(config),
                nebariHelmProvider(config),
            ]
        ),
    }


def stage_05_kubernetes_keycloak(config):
    return {
        "stages/05-kubernetes-keycloak/_nebari.tf.json": tf_render_objects(
            [
                nebariTerraformState("05-kubernetes-keycloak", config),
                nebariKubernetesProvider(config),
                nebariHelmProvider(config),
            ]
        ),
    }


def stage_06_kubernetes_keycloak_configuration(config):
    return {
        "stages/06-kubernetes-keycloak-configuration/_nebari.tf.json": tf_render_objects(
            [
                nebariTerraformState("06-kubernetes-keycloak-configuration", config),
            ]
        ),
    }


def stage_07_kubernetes_services(config):
    return {
        "stages/07-kubernetes-services/_nebari.tf.json": tf_render_objects(
            [
                nebariTerraformState("07-kubernetes-services", config),
                nebariKubernetesProvider(config),
                nebariHelmProvider(config),
            ]
        ),
    }


def stage_08_nebari_tf_extensions(config):
    return {
        "stages/08-nebari-tf-extensions/_nebari.tf.json": tf_render_objects(
            [
                nebariTerraformState("08-nebari-tf-extensions", config),
                nebariKubernetesProvider(config),
                nebariHelmProvider(config),
            ]
        ),
    }
