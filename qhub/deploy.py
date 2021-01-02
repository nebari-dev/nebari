import logging
from os import path
import os
import re
import json
from subprocess import check_output, run
from shutil import which

from qhub.utils import timer, change_directory, check_cloud_credentials
from qhub.provider.dns.cloudflare import update_record
from qhub.constants import SUPPORTED_TERRAFORM_MINOR_RELEASES

DO_ENV_DOCS = "https://github.com/Quansight/qhub/blob/master/docs/docs/do/installation.md#environment-variables"
AWS_ENV_DOCS = "https://github.com/Quansight/qhub/blob/master/docs/docs/aws/installation.md#environment-variables"
GCP_ENV_DOCS = "https://github.com/Quansight/qhub/blob/master/docs/docs/gcp/installation.md#environment-variables"


logger = logging.getLogger(__name__)


def deploy_configuration(config, dns_provider, dns_auto_provision, disable_prompt):
    logger.info(f'All qhub endpoints will be under *.{config["domain"]}')

    with timer(logger, "deploying QHub"):
        guided_install(config, dns_provider, dns_auto_provision, disable_prompt)


def guided_install(config, dns_provider, dns_auto_provision, disable_prompt=False):
    # 01 Verify configuration file exists
    verify_configuration_file_exists()

    # 02 Check terraform
    check_terraform()

    # 03 Check Environment Variables
    check_cloud_credentials(config)

    # 04 Check that oauth settings are set
    if not disable_prompt:
        input(
            'Ensure that oauth settings are in configuration [Press "Enter" to continue]'
        )

    # 05 Create terraform backend remote state bucket
    with change_directory("terraform-state"):
        run(["terraform", "init"])
        run(["terraform", "apply", "-auto-approve"])

    # 06 Create qhub initial state (up to nginx-ingress)
    with change_directory("infrastructure"):
        run(["terraform", "init"])
        run(
            [
                "terraform",
                "apply",
                "-auto-approve",
                "-target=module.kubernetes",
                "-target=module.kubernetes-initialization",
                "-target=module.kubernetes-ingress",
            ]
        )
        cmd_output = check_output(["terraform", "output", "--json"])
        try:
            output = json.loads(cmd_output)
        except json.decoder.JSONDecodeError as e:
            print(f"Failed to parse terraform output: {cmd_output}")
            raise e

    # 07 Update DNS to point to qhub deployment
    if dns_auto_provision and dns_provider == "cloudflare":
        record_name, zone_name = (
            config["domain"].split(".")[:-2],
            config["domain"].split(".")[-2:],
        )
        record_name = f'jupyter.{".".join(record_name)}'
        zone_name = ".".join(zone_name)
        ip = output["ingress_jupyter"]["value"]["ip"]
        if config["provider"] in {"do", "gcp"}:
            update_record(zone_name, record_name, "A", ip)
    else:
        input(
            f'Take IP Address {output["ingress_jupyter"]["value"]["ip"]} and update DNS to point to "jupyter.{config["domain"]}" [Press Enter when Complete]'
        )

    # 08 Full deploy QHub
    with change_directory("infrastructure"):
        run(["terraform", "apply", "-auto-approve"])
