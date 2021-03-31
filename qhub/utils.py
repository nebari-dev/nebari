import subprocess
import sys
import time
import os
import contextlib
from os import path

DO_ENV_DOCS = "https://github.com/Quansight/qhub/blob/master/docs/docs/do/installation.md#environment-variables"
AWS_ENV_DOCS = "https://github.com/Quansight/qhub/blob/master/docs/docs/aws/installation.md#environment-variables"
GCP_ENV_DOCS = "https://github.com/Quansight/qhub/blob/master/docs/docs/gcp/installation.md#environment-variables"
AZURE_ENV_DOCS = "Coming Soon"


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


def run_subprocess_cmd(*args, **kwargs):
    """Runs subprocess command with realtime stdout logging with optional line prefix"""
    if "prefix" in kwargs:
        line_prefix = f"[{kwargs['prefix']}]".encode("utf-8")
        kwargs.pop("prefix")
    else:
        line_prefix = b""

    process = subprocess.Popen(*args, **kwargs, stdout=subprocess.PIPE)
    for line in iter(lambda: process.stdout.readline(), b""):
        sys.stdout.buffer.write(line_prefix + line)
        sys.stdout.flush()


def check_cloud_credentials(config):
    if config["provider"] == "gcp":
        for variable in {"GOOGLE_CREDENTIALS"}:
            if variable not in os.environ:
                raise Exception(
                    f"""Missing the following required environment variable: {variable}\n
                    Please see the documentation for more information: {GCP_ENV_DOCS}"""
                )
    elif config["provider"] == "azure":
        for variable in {
            "ARM_CLIENT_ID",
            "ARM_CLIENT_SECRET",
            "ARM_SUBSCRIPTION_ID",
            "ARM_TENANT_ID",
        }:
            if variable not in os.environ:
                raise Exception(
                    f"""Missing the following required environment variable: {variable}\n
                    Please see the documentation for more information: {AZURE_ENV_DOCS}"""
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
    elif config["provider"] == "local":
        pass
    else:
        raise Exception("Cloud Provider configuration not supported")


def verify_configuration_file_exists():
    if not path.exists("qhub-config.yaml"):
        raise Exception('Configuration file "qhub-config.yaml" does not exist')
