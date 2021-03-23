import logging
from subprocess import run

from qhub.utils import (
    timer,
    change_directory,
    check_cloud_credentials,
    verify_configuration_file_exists,
)
from qhub.provider import terraform


logger = logging.getLogger(__name__)


def destroy_configuration(config):
    logger.info(
        """Removing all infrastructure, your local files will still remain, \n
    you can use 'qhub deploy' to re - install infrastructure using same config file"""
    )

    with timer(logger, "destroying QHub"):
        # 01 Verify configuration file exists
        verify_configuration_file_exists()

        # 02 Check Environment Variables
        check_cloud_credentials(config)

        # 03 Remove all infrastructure
        terraform.destroy(directory='infrastructure')

        # 06 Remove terraform backend remote state bucket
        # backwards compatible with `qhub-config.yaml` which
        # don't have `terraform_state` key
        if config.get("terraform_state") != "local":
            terraform.destroy(directory='terraform-state')
