import io
import os
import platform
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

from qhub.utils import run_subprocess_cmd, QHubError
from qhub import constants
from qhub.console import console


class TerraformError(QHubError):
    pass


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
        console.print(
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
    if run_subprocess_cmd([terraform_path] + processargs, **kwargs):
        raise TerraformError("Terraform returned an error")


def version():
    terraform_path = download_terraform_binary()
    command = [terraform_path, "--version"]
    version_output = subprocess.check_output(command, encoding="utf-8")
    return re.search(r"(\d+)\.(\d+).(\d+)", version_output).group(0)


def init(directory=None):
    command = ["init"]
    run_terraform_subprocess(command, cwd=directory, prefix="terraform")


def apply(directory=None, targets=None):
    targets = targets or []
    command = ["apply", "-auto-approve"] + ["-target=" + _ for _ in targets]
    run_terraform_subprocess(command, cwd=directory, prefix="terraform")


def output(directory=None):
    terraform_path = download_terraform_binary()
    command = [terraform_path, "output", "-json"]
    return subprocess.check_output(command, cwd=directory, encoding="utf-8")[:-1]


def tfimport(addr, id, directory=None):
    command = ["import", addr, id]
    run_terraform_subprocess(
        command, cwd=directory, prefix="terraform"
    )


def refresh(directory=None):
    command = [
        "refresh",
    ]
    run_terraform_subprocess(command, cwd=directory, prefix="terraform")


def destroy(directory=None):
    command = ["destroy", "-auto-approve"]
    run_terraform_subprocess(command, cwd=directory, prefix="terraform")


def rm_local_state(directory=None):
    tfstate_path = "terraform.tfstate"
    if directory:
        tfstate_path = os.path.join(directory, tfstate_path)

    if os.path.isfile(tfstate_path):
        os.remove(tfstate_path)
