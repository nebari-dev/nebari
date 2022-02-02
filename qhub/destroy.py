import logging
import os
import tempfile

from qhub.utils import timer, check_cloud_credentials
from qhub.provider import terraform

logger = logging.getLogger(__name__)


def destroy_01_terraform_state(config):
    directory = "stages/01-terraform-state"

    if config["provider"] == "local":
        pass
    elif config["provider"] == "do":
        terraform.deploy(
            terraform_import=True,
            # acl and force_destroy do not import properly
            # and only get refreshed properly with an apply
            terraform_apply=True,
            terraform_destroy=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "namespace": config["namespace"],
                "region": config["digital_ocean"]["region"],
            },
            state_imports=[
                (
                    "module.terraform-state.module.spaces.digitalocean_spaces_bucket.main",
                    f"{config['digital_ocean']['region']},{config['project_name']}-{config['namespace']}-terraform-state",
                )
            ],
        )
    elif config["provider"] == "gcp":
        terraform.deploy(
            terraform_import=True,
            # acl and force_destroy do not import properly
            # and only get refreshed properly with an apply
            terraform_apply=True,
            terraform_destroy=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "namespace": config["namespace"],
                "region": config["google_cloud_platform"]["region"],
            },
            state_imports=[
                (
                    "module.terraform-state.module.gcs.google_storage_bucket.static-site",
                    f"{config['project_name']}-{config['namespace']}-terraform-state",
                )
            ],
        )
    elif config["provider"] == "azure":
        subscription_id = os.environ["ARM_SUBSCRIPTION_ID"]
        resource_group_name = f"{config['project_name']}-{config['namespace']}"
        resource_group_name_safe = resource_group_name.replace("-", "")
        resource_group_url = f"/subscriptions/{subscription_id}/resourceGroups/{config['project_name']}-{config['namespace']}"

        terraform.deploy(
            terraform_import=True,
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "namespace": config["namespace"],
                "region": config["azure"]["region"],
                "storage_account_postfix": config["azure"]["storage_account_postfix"],
            },
            state_imports=[
                (
                    "module.terraform-state.azurerm_resource_group.terraform-resource-group",
                    resource_group_url,
                ),
                (
                    "module.terraform-state.azurerm_storage_account.terraform-storage-account",
                    f"{resource_group_url}/providers/Microsoft.Storage/storageAccounts/{resource_group_name_safe}{config['azure']['storage_account_postfix']}",
                ),
                (
                    "module.terraform-state.azurerm_storage_container.storage_container",
                    f"https://{resource_group_name_safe}{config['azure']['storage_account_postfix']}.blob.core.windows.net/{resource_group_name}state",
                ),
            ],
        )
    elif config["provider"] == "aws":
        terraform.deploy(
            terraform_import=True,
            # acl and force_destroy do not import properly
            # and only get refreshed properly with an apply
            terraform_apply=True,
            terraform_destroy=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "namespace": config["namespace"],
            },
            state_imports=[
                (
                    "module.terraform-state.aws_s3_bucket.terraform-state",
                    f"{config['project_name']}-{config['namespace']}-terraform-state",
                ),
                (
                    "module.terraform-state.aws_dynamodb_table.terraform-state-lock",
                    f"{config['project_name']}-{config['namespace']}-terraform-state-lock",
                ),
            ],
        )
    else:
        raise NotImplementedError(
            f'provider {config["provider"]} not implemented for directory={directory}'
        )


def destroy_02_infrastructure(config):
    directory = "stages/02-infrastructure"

    if config["provider"] == "local":
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={"kube_context": config["local"].get("kube_context")},
        )
    elif config["provider"] == "do":
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "environment": config["namespace"],
                "region": config["digital_ocean"]["region"],
                "kubernetes_version": config["digital_ocean"]["kubernetes_version"],
                "node_groups": config["digital_ocean"]["node_groups"],
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "QHUB_KUBECONFIG"
                ),
            },
        )
    elif config["provider"] == "gcp":
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "environment": config["namespace"],
                "region": config["google_cloud_platform"]["region"],
                "project_id": config["google_cloud_platform"]["project"],
                "node_groups": [
                    {
                        "name": key,
                        "min_size": value["min_nodes"],
                        "max_size": value["max_nodes"],
                        **value,
                    }
                    for key, value in config["google_cloud_platform"][
                        "node_groups"
                    ].items()
                ],
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "QHUB_KUBECONFIG"
                ),
            },
        )
    elif config["provider"] == "azure":
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "environment": config["namespace"],
                "region": config["azure"]["region"],
                "kubernetes_version": config["azure"]["kubernetes_version"],
                "node_groups": config["azure"]["node_groups"],
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "QHUB_KUBECONFIG"
                ),
            },
        )
    elif config["provider"] == "aws":
        terraform.deploy(
            terraform_apply=False,
            terraform_destroy=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "environment": config["namespace"],
                "node_groups": [
                    {
                        "name": key,
                        "min_size": value["min_nodes"],
                        "desired_size": value["min_nodes"],
                        "max_size": value["max_nodes"],
                        "gpu": value.get("gpu", False),
                        "instance_type": value["instance"],
                    }
                    for key, value in config["amazon_web_services"][
                        "node_groups"
                    ].items()
                ],
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "QHUB_KUBECONFIG"
                ),
            },
        )
    else:
        raise NotImplementedError(
            f'provider {config["provider"]} not implemented for directory={directory}'
        )


def destroy_configuration(config):
    logger.info(
        """Removing all infrastructure, your local files will still remain,
    you can use 'qhub deploy' to re-install infrastructure using same config file\n"""
    )

    with timer(logger, "destroying QHub"):
        # 01 Check Environment Variables
        check_cloud_credentials(config)

        destroy_02_infrastructure(config)
        destroy_01_terraform_state(config)
