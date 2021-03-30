import io
import logging
import os
import platform
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

from qhub.utils import timer, run_subprocess_cmd
from qhub import constants


logger = logging.getLogger(__name__)


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


def version():
    terraform_path = download_terraform_binary()
    logger.info(f"checking terraform={terraform_path} version")

    version_output = subprocess.check_output([terraform_path, "--version"]).decode(
        "utf-8"
    )
    return re.search(r"(\d+)\.(\d+).(\d+)", version_output).group(0)


def init(directory=None):
    terraform_path = download_terraform_binary()
    logger.info(f"terraform={terraform_path} init directory={directory}")
    with timer(logger, "terraform init"):
        run_subprocess_cmd([terraform_path, "init"], cwd=directory)


def apply(directory=None, targets=None):
    targets = targets or []
    terraform_path = download_terraform_binary()

    logger.info(
        f"terraform={terraform_path} apply directory={directory} targets={targets}"
    )
    command = [terraform_path, "apply", "-auto-approve"] + [
        "-target=" + _ for _ in targets
    ]
    with timer(logger, "terraform apply"):
        run_subprocess_cmd(command, cwd=directory)


def output(directory=None):
    terraform_path = download_terraform_binary()

    logger.info(f"terraform={terraform_path} output directory={directory}")
    with timer(logger, "terraform output"):
        return subprocess.check_output(
            [terraform_path, "output", "-json"], cwd=directory
        ).decode("utf8")[:-1]


def destroy(directory=None):
    terraform_path = download_terraform_binary()

    logger.info(f"terraform={terraform_path} destroy directory={directory}")

    with timer(logger, "terraform destroy"):
        subprocess.check_output(
            [
                terraform_path,
                "destroy",
                "-auto-approve",
            ],
            cwd=directory,
        )
