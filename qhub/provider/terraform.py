import io
import json
import logging
import os
import platform
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from typing import Dict, Any

from qhub.utils import timer, run_subprocess_cmd, modified_environ
from qhub import constants


logger = logging.getLogger(__name__)


class TerraformException(Exception):
    pass


def deploy(directory, input_vars: Dict[str, Any] = None):
    """Execute a given terraform directory

    """
    input_vars = input_vars or {}

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix='.tfvars.json') as f:
        json.dump(input_vars, f.file)
        f.file.flush()

        init(directory)
        apply(directory, var_files=[f.name])
        return output(directory)


def download_terraform_binary(version=constants.TERRAFORM_VERSION):
    os_mapping = {
        "linux": "linux",
        "win32": "windows",
        "darwin": "darwin",
        "freebsd": "freebsd",
        "openbsd": "openbsd",
        "solaris": "solaris",
    }

    architecture_mapping = {
        "x86_64": "amd64",
        "i386": "386",
        "armv7l": "arm",
        "aarch64": "arm64",
    }

    download_url = f"https://releases.hashicorp.com/terraform/{version}/terraform_{version}_{os_mapping[sys.platform]}_{architecture_mapping[platform.machine()]}.zip"
    filename_directory = os.path.join(tempfile.gettempdir(), "terraform", version)
    filename_path = os.path.join(filename_directory, "terraform")

    if not os.path.isfile(filename_path):
        logger.info(
            f"downloading and extracting terraform binary from url={download_url} to path={filename_path}"
        )
        with urllib.request.urlopen(download_url) as f:
            bytes_io = io.BytesIO(f.read())
        download_file = zipfile.ZipFile(bytes_io)
        download_file.extract("terraform", filename_directory)

    os.chmod(filename_path, 0o555)
    return filename_path


def run_terraform_subprocess(processargs, **kwargs):
    terraform_path = download_terraform_binary()
    logger.info(f" terraform at {terraform_path}")
    if run_subprocess_cmd([terraform_path] + processargs, **kwargs):
        raise TerraformException("Terraform returned an error")


def version():
    terraform_path = download_terraform_binary()
    logger.info(f"checking terraform={terraform_path} version")

    version_output = subprocess.check_output([terraform_path, "--version"]).decode(
        "utf-8"
    )
    return re.search(r"(\d+)\.(\d+).(\d+)", version_output).group(0)


def init(directory=None):
    logger.info(f"terraform init directory={directory}")
    with timer(logger, "terraform init"):
        run_terraform_subprocess(["init"], cwd=directory, prefix="terraform")


def apply(directory=None, targets=None, var_files=None):
    targets = targets or []
    var_files = var_files or []

    logger.info(f"terraform apply directory={directory} targets={targets}")
    command = ["apply", "-auto-approve"] + ["-target=" + _ for _ in targets] + ["-var-file=" + _ for _ in var_files]
    with timer(logger, "terraform apply"):
        run_terraform_subprocess(command, cwd=directory, prefix="terraform")


def output(directory=None):
    terraform_path = download_terraform_binary()

    logger.info(f"terraform={terraform_path} output directory={directory}")
    with timer(logger, "terraform output"):
        return json.loads(subprocess.check_output(
            [terraform_path, "output", "-json"], cwd=directory
        ).decode("utf8")[:-1])


def tfimport(addr, id, directory=None):
    logger.info(f"terraform import directory={directory} addr={addr} id={id}")
    command = ["import", addr, id]
    with timer(logger, "terraform import"):
        run_terraform_subprocess(
            command, cwd=directory, prefix="terraform", strip_errors=True, timeout=30
        )


def refresh(directory=None):
    logger.info(f"terraform refresh directory={directory}")
    command = [
        "refresh",
    ]

    with timer(logger, "terraform refresh"):
        run_terraform_subprocess(command, cwd=directory, prefix="terraform")


def destroy(directory=None, targets=None):
    targets = targets or []

    logger.info(f"terraform destroy directory={directory} targets={targets}")
    command = [
        "destroy",
        "-auto-approve",
    ] + ["-target=" + _ for _ in targets]

    with timer(logger, "terraform destroy"):
        run_terraform_subprocess(command, cwd=directory, prefix="terraform")


def rm_local_state(directory=None):
    logger.info(f"rm local state file terraform.tfstate directory={directory}")
    tfstate_path = "terraform.tfstate"
    if directory:
        tfstate_path = os.path.join(directory, tfstate_path)

    if os.path.isfile(tfstate_path):
        os.remove(tfstate_path)
