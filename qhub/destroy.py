import logging
from subprocess import run

from qhub.utils import timer, change_directory, check_cloud_credentials, verify_configuration_file_exists, check_terraform


logger = logging.getLogger(__name__)


def destroy_configuration(config):
    logger.info("""Removing all infrastructure, your local files will still remain, \n
    you can use 'qhub deploy' to re - install infrastructure using same config file""")

    with timer(logger, "destroying QHub"):
        # 01 Verify configuration file exists
        verify_configuration_file_exists()

        # 02 Check terraform
        check_terraform()

        # 03 Check Environment Variables
        check_cloud_credentials(config)

        # 04 Remove all infrastructure
        with change_directory("infrastructure"):
            run(["terraform", "destroy", "-auto-approve"])

        # 06 Remove terraform backend remote state bucket
        with change_directory("terraform-state"):
            run(["terraform", "destroy", "-auto-approve"])
