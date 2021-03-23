import subprocess
import logging
import json
import sys
import stat
import platform
import urllib.request
import zipfile
import io
import os
import tempfile
import shutil


from qhub.utils import timer
from qhub import constants


logger = logging.getLogger(__name__)


def download_terraform_binary(version=None):
    version = version or constants.DEFAULT_TERRAFORM_VERSION

    os_mapping = {
        'linux': 'linux',
        'win32': 'windows',
        'darwin': 'darwin',
        'freebsd': 'freebsd',
        'openbsd': 'openbsd',
        'solaris': 'solaris',
    }

    architecture_mapping = {
        'x86_64': 'amd64',
        'i386': '386',
        'armv7l': 'arm',
        'aarch64': 'arm64',
    }

    download_url = f'https://releases.hashicorp.com/terraform/{version}/terraform_{version}_{os_mapping[sys.platform]}_{architecture_mapping[platform.machine()]}.zip'
    filename_directory = os.path.join(tempfile.gettempdir(), 'terraform', version)
    filename_path = os.path.join(filename_directory, 'terraform')

    if not os.path.isfile(filename_path):
        logger.info('downloading and extracting terraform binary from url={download_url} to path={filename_path}')
        with urllib.request.urlopen(download_url) as f:
            bytes_io = io.BytesIO(f.read())
        download_file = zipfile.ZipFile(bytes_io)
        download_file.extract('terraform', filename_directory)

    os.chmod(filename_path, 0o555)
    return filename_path


def version(terraform_path="terraform"):
    terraform_path = shutil.which(terraform_path) or download_terraform_binary()
    logger.info(f'checking terraform={terraform_path} version')

    version_output = subprocess.check_output([terraform_path, "--version"]).decode("utf-8")
    return re.search(r"(\d+)\.(\d+).(\d+)", version_output).group(0)


def init(terraform_path='terraform', directory=None):
    terraform_path = shutil.which(terraform_path) or download_terraform_binary()

    logger.info(f"terraform={terraform_path} init directory={directory}")
    with timer(logger, "terraform init"):
        subprocess.check_output([terraform_path, "init"], shell=True, cwd=directory)


def apply(terraform_path='terraform', directory=None, targets=None):
    targets = targets or []
    terraform_path = shutil.which(terraform_path) or download_terraform_binary()

    logger.info(f"terraform={terraform_path} apply directory={directory} targets={targets}")
    with timer(logger, "terraform apply"):
        command = " ".join(
            [terraform_path, "apply", "-auto-approve"] + ["-target=" + _ for _ in targets]
        )

        subprocess.check_output(command, shell=True, cwd=directory)


def output(terraform_path='terraform', directory=None):
    terraform_path = shutil.which(terraform_path) or download_terraform_binary()

    logger.info(f"terraform={terraform_path} output directory={directory}")
    with timer(logger, "terraform output"):
        output = subprocess.check_output(
            [terraform_path, "output", "-json"], shell=True, cwd=directory
        ).decode("utf8")
        return json.loads(output)


def destroy(terraform_path='terraform', directory=None):
    terraform_path = shutil.which(terraform_path) or download_terraform_binary()

    logger.info(f"terraform destroy directory={directory}")

    with timer(logger, "terraform destroy"):
        subprocess.check_output([
            terraform_path, "destroy", "-auto-approve",
        ], shell=True, cwd=directory)
