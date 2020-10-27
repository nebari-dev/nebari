import logging
from os import path, environ
import os
import re
import json
from subprocess import check_output
from shutil import which

from qhub.utils import timer, change_directory
from qhub.provider.dns.cloudflare import update_record


logger = logging.getLogger(__name__)


def deploy_configuration(config, dns_provider, dns_auto_provision):
    logger.info(f'All qhub endpoints will be under *.{config["domain"]}')

    with timer(logger, "deploying QHub"):
        guided_install(config)


def guided_install(config, dns_provider, dns_auto_provision):
    SUPPORTED_VERSIONS = ["v0.13"]

    # 01 Verify configuration file exists
    if not path.exists("qhub-config.yaml"):
        raise Exception('Configuration file "qhub-config.yaml" does not exist')

    # 02 Check if Terraform works
    if which("terraform") is None:
        raise Exception(
            f"Please install Terraform with one of the following minor releases: {SUPPORTED_VERSIONS}"
        )

    # 03 Check version of Terraform
    version_out = check_output(["terraform", "--version"]).decode("utf-8")
    minor_release = re.search(r"v(\d+)\.(\d+)", version_out).group(0)

    if minor_release not in SUPPORTED_VERSIONS:
        raise Exception(
            f"Unsupported Terraform version. Supported minor releases: {SUPPORTED_VERSIONS}"
        )

    # 04 Check Environment Variables
    if config["provider"] == "gcp":
        if "GOOGLE_CREDENTIALS" not in environ:
            raise Exception(
                """The environment variable "Google Credentials" doesn't exist. It must be set to the path that contains
                the GCP credentials json file. Instructions for creating this file can be found here:
                https://cloud.google.com/iam/docs/creating-managing-service-account-keys
                """
            )
    elif config["provider"] == "aws":
        if (
            "AWS_ACCESS_KEY_ID" not in environ
            or "AWS_SECRET_ACCESS_KEY" not in environ
            or "AWS_DEFAULT_REGION" not in environ
        ):
            print(
                "The following environment variables are required for AWS: (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION) must be set"
            )
    elif config["provider"] == "do":
        do_env_docs = "https://qhub.readthedocs.io/en/latest/docs/do/installation.html#environment-variables"
        required_variables = [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "SPACES_ACCESS_KEY_ID",
            "SPACES_SECRET_ACCESS_KEY",
            "DIGITALOCEAN_TOKEN",
        ]

        missing_variables = [_ for _ in required_variables if _ not in environ]

        if len(missing_variables) > 0:
            raise Exception(
                f"""Missing the following required environment variables: {required_variables}
        \n
        Please see the documentation for more information: {do_env_docs}
            """
            )

        if environ["AWS_ACCESS_KEY_ID"] != environ["SPACES_ACCESS_KEY_ID"]:
            raise Exception(
                f"""The environment variables AWS_ACCESS_KEY_ID and SPACES_ACCESS_KEY_ID must equal each other.
            \n
        See {do_env_docs} for more information"""
            )

        if environ["AWS_SECRET_ACCESS_KEY"] != environ["SPACES_SECRET_ACCESS_KEY"]:
            raise Exception(
                f"""The environment variables AWS_SECRET_ACCESS_KEY and SPACES_SECRET_ACCESS_KEY must equal each other.
            \n
        See {do_env_docs} for more information"""
            )
    else:
        raise Exception("Cloud Provider configuration not supported")

    # 05 Check that oauth settings are set
    input('Ensure that oauth settings are in configuration [Press "Enter" to continue]')

    # 06 Create terraform backend remote state bucket
    with change_directory('terraform-state'):
        check_output(['terraform', 'init'])
        check_output(['terraform', 'apply', '-auto-approve'])

    # 07 Create qhub initial state (up to nginx-ingress)
    with change_directory('infrastructure'):
        check_output(['terraform', 'init'])
        check_output([
            "terraform", "apply", "-auto-approve",
            "-target=module.kubernetes",
            "-target=module.kubernetes-initialization",
            "-target=module.kubernetes-ingress"
        ])
        output = json.loads(check_output([
            "terraform", "output", "--json"
        ]))

    # 08 Update DNS to point to qhub deployment
    if dns_auto_provision and dns_provider == 'cloudflare':
        record_name, zone_name = config['domain'].split('.')
        record_name = f'jupyter.{".".join(record_name)}'
        zone_name = '.'.join(zone_name)
        ip = output['ingress_jupyter']['value']['ip']
        if config['provider'] in {'do', 'gcp'}:
            update_record(zone_name, record_name, 'A', ip)
    else:
        input(
            f'Take IP Address Above and update DNS to point to "jupyter.{config["domain"]}" [Press Enter when Complete]'
        )

    # 09 Full deploy QHub
    check_output(['terraform', 'apply', '-auto-approve'])
