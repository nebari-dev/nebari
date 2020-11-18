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
    if not path.exists("qhub-config.yaml"):
        raise Exception('Configuration file "qhub-config.yaml" does not exist')

    # 02 Check if Terraform works
    if which("terraform") is None:
        raise Exception(
            f"Please install Terraform with one of the following minor releases: {SUPPORTED_TERRAFORM_MINOR_RELEASES}"
        )

    # 03 Check version of Terraform
    version_out = check_output(["terraform", "--version"]).decode("utf-8")
    minor_release = re.search(r"(\d+)\.(\d+)", version_out).group(0)

    if minor_release not in SUPPORTED_TERRAFORM_MINOR_RELEASES:
        raise Exception(
            f"Unsupported Terraform version. Supported minor releases: {SUPPORTED_TERRAFORM_MINOR_RELEASES}"
        )

    # 04 Check Environment Variables
    if config["provider"] == "gcp":
        for variable in {"GOOGLE_CREDENTIALS"}:
            if variable not in os.environ:
                raise Exception(
                    f"""Missing the following required environment variable: {variable}\n
                    Please see the documentation for more information: {GCP_ENV_DOCS}"""
                )
    elif config["provider"] == "aws":
        for variable in {
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_DEFAULT_REGION",
        }:
            if variable not in os.environ:
                raise Exception(
                    f"""Missing the following required environment variable: {variable}\n
                    Please see the documentation for more information: {AWS_ENV_DOCS}"""
                )
    elif config["provider"] == "do":
        for variable in {
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "SPACES_ACCESS_KEY_ID",
            "SPACES_SECRET_ACCESS_KEY",
            "DIGITALOCEAN_TOKEN",
        }:
            if variable not in os.environ:
                raise Exception(
                    f"""Missing the following required environment variable: {variable}\n
                    Please see the documentation for more information: {DO_ENV_DOCS}"""
                )

        if os.environ["AWS_ACCESS_KEY_ID"] != os.environ["SPACES_ACCESS_KEY_ID"]:
            raise Exception(
                f"""The environment variables AWS_ACCESS_KEY_ID and SPACES_ACCESS_KEY_ID must be equal\n
                See {DO_ENV_DOCS} for more information"""
            )

        if (
            os.environ["AWS_SECRET_ACCESS_KEY"]
            != os.environ["SPACES_SECRET_ACCESS_KEY"]
        ):
            raise Exception(
                f"""The environment variables AWS_SECRET_ACCESS_KEY and SPACES_SECRET_ACCESS_KEY must be equal\n
                See {DO_ENV_DOCS} for more information"""
            )
    else:
        raise Exception("Cloud Provider configuration not supported")

    # 05 Check that oauth settings are set
    if not disable_prompt:
        input(
            'Ensure that oauth settings are in configuration [Press "Enter" to continue]'
        )

    # 06 Create terraform backend remote state bucket
    with change_directory("terraform-state"):
        run(["terraform", "init"])
        run(["terraform", "apply", "-auto-approve"])

    # 07 Create qhub initial state (up to nginx-ingress)
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
        output = json.loads(check_output(["terraform", "output", "--json"]))

    # 08 Update DNS to point to qhub deployment
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

    # 09 Full deploy QHub
    with change_directory("infrastructure"):
        run(["terraform", "apply", "-auto-approve"])
