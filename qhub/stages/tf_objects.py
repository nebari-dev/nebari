from typing import Dict

from qhub.provider.terraform import Data, Provider, TerraformBackend, tf_render_objects
from qhub.utils import deep_merge


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
    if qhub_config["provider"] == "aws":
        cluster_name = f"{qhub_config['project_name']}-{qhub_config['namespace']}"
        # The AWS provider needs to be added, as we are using aws related resources #1254
        return deep_merge(
            Data("aws_eks_cluster", "default", name=cluster_name),
            Data("aws_eks_cluster_auth", "default", name=cluster_name),
            Provider("aws", region=qhub_config["amazon_web_services"]["region"]),
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


def QHubHelmProvider(qhub_config: Dict):
    if qhub_config["provider"] == "aws":
        cluster_name = f"{qhub_config['project_name']}-{qhub_config['namespace']}"

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
            resource_group_name=f"{qhub_config['project_name']}-{qhub_config['namespace']}-state",
            # storage account must be globally unique
            storage_account_name=f"{qhub_config['project_name']}{qhub_config['namespace']}{qhub_config['azure']['storage_account_postfix']}",
            container_name=f"{qhub_config['project_name']}-{qhub_config['namespace']}-state",
            key=f"terraform/{qhub_config['project_name']}-{qhub_config['namespace']}/{directory}",
        )
    elif qhub_config["provider"] == "existing":
        optional_kwargs = {}
        if "kube_context" in qhub_config["existing"]:
            optional_kwargs["confix_context"] = qhub_config["existing"]["kube_context"]
        return TerraformBackend(
            "kubernetes",
            secret_suffix=f"{qhub_config['project_name']}-{qhub_config['namespace']}-{directory}",
            load_config_file=True,
            **optional_kwargs,
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


def stage_01_terraform_state(config):
    if config["provider"] == "gcp":
        return {
            "stages/01-terraform-state/gcp/_qhub.tf.json": tf_render_objects(
                [
                    QHubGCPProvider(config),
                ]
            )
        }
    elif config["provider"] == "aws":
        return {
            "stages/01-terraform-state/aws/_qhub.tf.json": tf_render_objects(
                [
                    QHubAWSProvider(config),
                ]
            )
        }
    else:
        return {}


def stage_02_infrastructure(config):
    if config["provider"] == "gcp":
        return {
            "stages/02-infrastructure/gcp/_qhub.tf.json": tf_render_objects(
                [
                    QHubGCPProvider(config),
                    QHubTerraformState("02-infrastructure", config),
                ]
            )
        }
    elif config["provider"] == "do":
        return {
            "stages/02-infrastructure/do/_qhub.tf.json": tf_render_objects(
                [
                    QHubTerraformState("02-infrastructure", config),
                ]
            )
        }
    elif config["provider"] == "azure":
        return {
            "stages/02-infrastructure/azure/_qhub.tf.json": tf_render_objects(
                [
                    QHubTerraformState("02-infrastructure", config),
                ]
            ),
        }
    elif config["provider"] == "aws":
        return {
            "stages/02-infrastructure/aws/_qhub.tf.json": tf_render_objects(
                [
                    QHubAWSProvider(config),
                    QHubTerraformState("02-infrastructure", config),
                ]
            )
        }
    else:
        return {}


def stage_03_kubernetes_initialize(config):
    return {
        "stages/03-kubernetes-initialize/_qhub.tf.json": tf_render_objects(
            [
                QHubTerraformState("03-kubernetes-initialize", config),
                QHubKubernetesProvider(config),
                QHubHelmProvider(config),
            ]
        ),
    }


def stage_04_kubernetes_ingress(config):
    return {
        "stages/04-kubernetes-ingress/_qhub.tf.json": tf_render_objects(
            [
                QHubTerraformState("04-kubernetes-ingress", config),
                QHubKubernetesProvider(config),
                QHubHelmProvider(config),
            ]
        ),
    }


def stage_05_kubernetes_keycloak(config):
    return {
        "stages/05-kubernetes-keycloak/_qhub.tf.json": tf_render_objects(
            [
                QHubTerraformState("05-kubernetes-keycloak", config),
                QHubKubernetesProvider(config),
                QHubHelmProvider(config),
            ]
        ),
    }


def stage_06_kubernetes_keycloak_configuration(config):
    return {
        "stages/06-kubernetes-keycloak-configuration/_qhub.tf.json": tf_render_objects(
            [
                QHubTerraformState("06-kubernetes-keycloak-configuration", config),
            ]
        ),
    }


def stage_07_kubernetes_services(config):
    return {
        "stages/07-kubernetes-services/_qhub.tf.json": tf_render_objects(
            [
                QHubTerraformState("07-kubernetes-services", config),
                QHubKubernetesProvider(config),
                QHubHelmProvider(config),
            ]
        ),
    }


def stage_08_qhub_tf_extensions(config):
    return {
        "stages/08-qhub-tf-extensions/_qhub.tf.json": tf_render_objects(
            [
                QHubTerraformState("08-qhub-tf-extensions", config),
                QHubKubernetesProvider(config),
                QHubHelmProvider(config),
            ]
        ),
    }
