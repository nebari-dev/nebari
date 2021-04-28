from .provider import terraform


def terraform_state_sync(config, logger=None):
    """
    Clear terraform-state terraform.tfstate and re-import from cloud (if exists)
    then terraform apply to ensure state is correct in cloud too
    """
    terraform.init(directory="terraform-state")

    provider = config.get("provider")
    project_name = config.get("project_name")
    namespace = config.get("namespace")

    terraform.rm_local_state(directory="terraform-state")

    # Example imports:

    # AWS
    # terraform import module.terraform-state.aws_s3_bucket.terraform-state qhubintgrtnaws-dev-terraform-state
    # terraform import module.terraform-state.aws_dynamodb_table.terraform-state-lock qhubintgrtnaws-dev-terraform-state-lock

    # GCP
    # terraform import module.terraform-state.module.gcs.google_storage_bucket.static-site qhubintgrtngcp-dev-terraform-state
    # But needs terraform apply to import force_destroy: https://github.com/hashicorp/terraform-provider-google/issues/1509

    try:
        if provider == "aws":
            terraform.tfimport(
                "module.terraform-state.aws_s3_bucket.terraform-state",
                f"{project_name}-{namespace}-terraform-state",
                directory="terraform-state",
            )
            terraform.tfimport(
                "module.terraform-state.aws_dynamodb_table.terraform-state-lock",
                f"{project_name}-{namespace}-terraform-state-lock",
                directory="terraform-state",
            )

        elif provider == "gcp":
            terraform.tfimport(
                "module.terraform-state.module.gcs.google_storage_bucket.static-site",
                f"{project_name}-{namespace}-terraform-state",
                directory="terraform-state",
            )

        elif provider == "do":
            do_region = config.get("digital_ocean", {}).get("region", "nyc3")

            terraform.tfimport(
                "module.terraform-state.module.spaces.digitalocean_spaces_bucket.main",
                f"{do_region},{project_name}-{namespace}-terraform-state",
                directory="terraform-state",
            )

        elif provider == "azure":
            raise Exception("Need to import azure terraform-state")

    except terraform.TerraformException:
        if logger:
            logger.info(
                "Terraform error presumed to be due to importing a resource which does not exist yet"
            )

    terraform.apply(
        directory="terraform-state"
    )  # If before destroy, this is mainly to sync force_destroy attribute to buckets
    # If before deploy, this may be to create the resources for the first time
