import subprocess
import sys
import time
import os
import re
import contextlib
from typing import Sequence, Set

from .version import __version__

DO_ENV_DOCS = (
    "https://docs.qhub.dev/en/latest/source/02_get_started/02_setup.html#digital-ocean"
)
AWS_ENV_DOCS = "https://docs.qhub.dev/en/latest/source/02_get_started/02_setup.html#amazon-web-services-aws"
GCP_ENV_DOCS = "https://docs.qhub.dev/en/latest/source/02_get_started/02_setup.html#google-cloud-platform"
AZURE_ENV_DOCS = "https://docs.qhub.dev/en/latest/source/02_get_started/02_setup.html#microsoft-azure"

qhub_image_tag = f"v{__version__}"
pip_install_qhub = f"pip install qhub=={__version__}"

QHUB_GH_BRANCH = os.environ.get("QHUB_GH_BRANCH", "")
if QHUB_GH_BRANCH:
    qhub_image_tag = QHUB_GH_BRANCH
    pip_install_qhub = (
        f"pip install https://github.com/Quansight/qhub/archive/{QHUB_GH_BRANCH}.zip"
    )


# Regex for suitable project names
namestr_regex = r"^[A-Za-z][A-Za-z\-_]*[A-Za-z]$"


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


def run_subprocess_cmd(processargs, **kwargs):
    """Runs subprocess command with realtime stdout logging with optional line prefix."""
    if "prefix" in kwargs:
        line_prefix = f"[{kwargs['prefix']}]: ".encode("utf-8")
        kwargs.pop("prefix")
    else:
        line_prefix = b""

    strip_errors = kwargs.pop("strip_errors", False)

    process = subprocess.Popen(
        processargs, **kwargs, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    for line in iter(lambda: process.stdout.readline(), b""):
        full_line = line_prefix + line
        if strip_errors:
            full_line = full_line.decode("utf-8")
            full_line = re.sub(
                r"\x1b\[31m", "", full_line
            )  # Remove red ANSI escape code
            full_line = full_line.encode("utf-8")

        sys.stdout.buffer.write(full_line)
        sys.stdout.flush()
    return process.wait(
        timeout=10
    )  # Should already have finished because we have drained stdout


def check_cloud_credentials(config):
    if config["provider"] == "gcp":
        for variable in {"GOOGLE_CREDENTIALS"}:
            if variable not in os.environ:
                raise ValueError(
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
                raise ValueError(
                    f"""Missing the following required environment variable: {variable}\n
                    Please see the documentation for more information: {AZURE_ENV_DOCS}"""
                )
    elif config["provider"] == "aws":
        for variable in {
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        }:
            if variable not in os.environ:
                raise ValueError(
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
                raise ValueError(
                    f"""Missing the following required environment variable: {variable}\n
                    Please see the documentation for more information: {DO_ENV_DOCS}"""
                )

        if os.environ["AWS_ACCESS_KEY_ID"] != os.environ["SPACES_ACCESS_KEY_ID"]:
            raise ValueError(
                f"""The environment variables AWS_ACCESS_KEY_ID and SPACES_ACCESS_KEY_ID must be equal\n
                See {DO_ENV_DOCS} for more information"""
            )

        if (
            os.environ["AWS_SECRET_ACCESS_KEY"]
            != os.environ["SPACES_SECRET_ACCESS_KEY"]
        ):
            raise ValueError(
                f"""The environment variables AWS_SECRET_ACCESS_KEY and SPACES_SECRET_ACCESS_KEY must be equal\n
                See {DO_ENV_DOCS} for more information"""
            )
    elif config["provider"] == "local":
        pass
    else:
        raise ValueError("Cloud Provider configuration not supported")


def check_for_duplicates(users: Sequence[dict]) -> Set:
    uids = set([])
    for user, attrs in users.items():
        if attrs["uid"] in uids:
            raise TypeError(f"Found duplicate uid ({attrs['uid']}) for {user}.")
        else:
            uids.add(attrs["uid"])
    return users
