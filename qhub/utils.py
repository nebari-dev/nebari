import time
import os
import contextlib
import re
from os import path
from subprocess import check_output
from shutil import which

from qhub.constants import SUPPORTED_TERRAFORM_VERSIONS

DO_ENV_DOCS = "https://github.com/Quansight/qhub/blob/master/docs/docs/do/installation.md#environment-variables"
AWS_ENV_DOCS = "https://github.com/Quansight/qhub/blob/master/docs/docs/aws/installation.md#environment-variables"
GCP_ENV_DOCS = "https://github.com/Quansight/qhub/blob/master/docs/docs/gcp/installation.md#environment-variables"


@contextlib.contextmanager
def timer(logger, prefix):
    start_time = time.time()
    yield
    logger.info(f"{prefix} took {time.time() - start_time:.3f} [s]")


@contextlib.contextmanager
def change_directory(directory):
    current_directory = os.getcwd()
    os.chdir(directory)
    yield
    os.chdir(current_directory)


def check_cloud_credentials(config):
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


def check_terraform():
    # 01 Check if Terraform works
    if which("terraform") is None:
        raise Exception(
            f"Please install Terraform with one of the following minor releases: {SUPPORTED_TERRAFORM_VERSIONS}"
        )

    # 02 Check version of Terraform
    version_out = check_output(["terraform", "--version"]).decode("utf-8")
    minor_release = re.search(r"(\d+)\.(\d+).(\d+)", version_out).group(0)

    if minor_release not in SUPPORTED_TERRAFORM_VERSIONS:
        raise Exception(
            f"Unsupported Terraform version. Supported terraform version(s): {SUPPORTED_TERRAFORM_VERSIONS}"
        )


def verify_configuration_file_exists():
    if not path.exists("qhub-config.yaml"):
        raise Exception('Configuration file "qhub-config.yaml" does not exist')
