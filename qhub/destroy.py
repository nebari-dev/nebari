import logging

from .utils import timer, check_cloud_credentials
from .provider import terraform
from .state import terraform_state_sync

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
            terraform_state_sync(config)
            terraform.destroy(directory="terraform-state")
