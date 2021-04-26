import logging

from qhub.utils import timer, check_cloud_credentials
from qhub.provider import terraform


logger = logging.getLogger(__name__)


def destroy_configuration(config):
    logger.info(
        """Removing all infrastructure, your local files will still remain, \n
    you can use 'qhub deploy' to re - install infrastructure using same config file"""
    )

    with timer(logger, "destroying QHub"):
        # 01 Check Environment Variables
        check_cloud_credentials(config)

        # 02 Remove all infrastructure
        terraform.init(directory="infrastructure")
        terraform.destroy(directory="infrastructure")

        # 03 Remove terraform backend remote state bucket
        # backwards compatible with `qhub-config.yaml` which
        # don't have `terraform_state` key
        if (config.get("terraform_state", {}).get("type") == "remote") and (
            config.get("provider") != "local"
        ):
            terraform.init(directory="terraform-state")

            provider = config.get("provider")
            project_name = config.get("project_name")
            namespace = config.get("namespace")

            terraform.rm_local_state(directory="terraform-state")

            # TODO First need to do, e.g.:

            # AWS
            # terraform import module.terraform-state.aws_s3_bucket.terraform-state qhubintgrtnaws-dev-terraform-state
            # terraform import module.terraform-state.aws_dynamodb_table.terraform-state-lock qhubintgrtnaws-dev-terraform-state-lock

            # GCP
            # terraform import module.terraform-state.module.gcs.google_storage_bucket.static-site qhubintgrtngcp-dev-terraform-state
            # But needs terraform apply to import force_destroy: https://github.com/hashicorp/terraform-provider-google/issues/1509

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
                terraform.tfimport(
                    "module.terraform-state.module.spaces.digitalocean_spaces_bucket.main",
                    f"{project_name}-{namespace}-terraform-state",
                    directory="terraform-state",
                )

            elif provider == "azure":
                raise Exception("Need to import azure terraform-state")

            terraform.apply(
                directory="terraform-state"
            )  # Mainly to sync force_destroy attribute to buckets

            terraform.destroy(directory="terraform-state")
