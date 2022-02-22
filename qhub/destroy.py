import logging
import os

from qhub.utils import timer, check_cloud_credentials
from qhub.stages import input_vars, state_imports
from qhub.provider import terraform

logger = logging.getLogger(__name__)


def destroy_01_terraform_state(config):
    directory = "stages/01-terraform-state"

    terraform.deploy(
        terraform_import=True,
        # acl and force_destroy do not import properly
        # and only get refreshed properly with an apply
        terraform_apply=True,
        terraform_destroy=True,
        directory=os.path.join(directory, config["provider"]),
        input_vars=input_vars.stage_01_terraform_state({}, config),
        state_imports=state_imports.stage_01_terraform_state({}, config),
    )


def destroy_02_infrastructure(config):
    directory = "stages/02-infrastructure"

    terraform.deploy(
        terraform_apply=False,
        terraform_destroy=True,
        directory=os.path.join(directory, config["provider"]),
        input_vars=input_vars.stage_02_infrastructure({}, config),
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
        if (
            config["provider"] != "local"
            and config["terraform_state"]["type"] == "remote"
        ):
            destroy_01_terraform_state(config)
