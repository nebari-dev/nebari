import os


def stage_01_terraform_state(stage_outputs, config):
    if config["provider"] == "do":
        return [
            (
                "module.terraform-state.module.spaces.digitalocean_spaces_bucket.main",
                f"{config['digital_ocean']['region']},{config['project_name']}-{config['namespace']}-terraform-state",
            )
        ]
    elif config["provider"] == "gcp":
        return [
            (
                "module.terraform-state.module.gcs.google_storage_bucket.static-site",
                f"{config['project_name']}-{config['namespace']}-terraform-state",
            )
        ]
    elif config["provider"] == "azure":
        subscription_id = os.environ["ARM_SUBSCRIPTION_ID"]
        resource_name_prefix = f"{config['project_name']}-{config['namespace']}"
        state_resource_group_name = f"{resource_name_prefix}-state"
        state_resource_name_prefix_safe = resource_name_prefix.replace("-", "")
        resource_group_url = f"/subscriptions/{subscription_id}/resourceGroups/{state_resource_group_name}"

        return [
            (
                "module.terraform-state.azurerm_resource_group.terraform-state-resource-group",
                resource_group_url,
            ),
            (
                "module.terraform-state.azurerm_storage_account.terraform-state-storage-account",
                f"{resource_group_url}/providers/Microsoft.Storage/storageAccounts/{state_resource_name_prefix_safe}{config['azure']['storage_account_postfix']}",
            ),
            (
                "module.terraform-state.azurerm_storage_container.storage_container",
                f"https://{state_resource_name_prefix_safe}{config['azure']['storage_account_postfix']}.blob.core.windows.net/{resource_name_prefix}-state",
            ),
        ]
    elif config["provider"] == "aws":
        return [
            (
                "module.terraform-state.aws_s3_bucket.terraform-state",
                f"{config['project_name']}-{config['namespace']}-terraform-state",
            ),
            (
                "module.terraform-state.aws_dynamodb_table.terraform-state-lock",
                f"{config['project_name']}-{config['namespace']}-terraform-state-lock",
            ),
        ]
