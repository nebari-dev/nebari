import logging
from os import path
import os
import re
import json
from subprocess import check_output, run
from shutil import which

from qhub.utils import timer, change_directory
from qhub.provider.dns.cloudflare import update_record
from qhub.constants import SUPPORTED_TERRAFORM_MINOR_RELEASES


logger = logging.getLogger(__name__)


def destroy_configuration(config):
    logger.info(f'Removing all infrastructure, your local files will still remain,
                you can use `qhub deploy` to re - install infrastructure using same config file')

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
