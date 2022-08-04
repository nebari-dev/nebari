import contextlib
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
from typing import Any, Dict, List

from qhub import constants
from qhub.utils import deep_merge, run_subprocess_cmd, timer

logger = logging.getLogger(__name__)


class TerraformException(Exception):
    pass


def deploy(
    directory,
    terraform_init: bool = True,
    terraform_import: bool = False,
    terraform_apply: bool = True,
    terraform_destroy: bool = False,
    input_vars: Dict[str, Any] = None,
    state_imports: List = None,
):
    """Execute a given terraform directory

    Parameters:
      directory: directory in which to run terraform operations on

      terraform_init: whether to run `terraform init` default True

      terraform_import: whether to run `terraform import` default
        False for each `state_imports` supplied to function

      terraform_apply: whether to run `terraform apply` default True

      terraform_destroy: whether to run `terraform destroy` default
        False

      input_vars: supply values for "variable" resources within
        terraform module

      state_imports: (addr, id) pairs for iterate through and attempt
        to terraform import
    """
    input_vars = input_vars or {}
    state_imports = state_imports or []

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".tfvars.json"
    ) as f:
        json.dump(input_vars, f.file)
        f.file.flush()

        if terraform_init:
            init(directory)

        if terraform_import:
            for addr, id in state_imports:
                tfimport(
                    addr, id, directory=directory, var_files=[f.name], exist_ok=True
                )

        if terraform_apply:
            apply(directory, var_files=[f.name])

        if terraform_destroy:
            destroy(directory, var_files=[f.name])

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
        "arm64": "arm64",
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


def init(directory=None, upgrade=True):
    logger.info(f"terraform init directory={directory}")
    with timer(logger, "terraform init"):
        command = ["init"]
        if upgrade:
            command.append("-upgrade")
        run_terraform_subprocess(command, cwd=directory, prefix="terraform")


def apply(directory=None, targets=None, var_files=None):
    targets = targets or []
    var_files = var_files or []

    logger.info(f"terraform apply directory={directory} targets={targets}")
    command = (
        ["apply", "-auto-approve"]
        + ["-target=" + _ for _ in targets]
        + ["-var-file=" + _ for _ in var_files]
    )
    with timer(logger, "terraform apply"):
        run_terraform_subprocess(command, cwd=directory, prefix="terraform")


def output(directory=None):
    terraform_path = download_terraform_binary()

    logger.info(f"terraform={terraform_path} output directory={directory}")
    with timer(logger, "terraform output"):
        return json.loads(
            subprocess.check_output(
                [terraform_path, "output", "-json"], cwd=directory
            ).decode("utf8")[:-1]
        )


def tfimport(addr, id, directory=None, var_files=None, exist_ok=False):
    var_files = var_files or []

    logger.info(f"terraform import directory={directory} addr={addr} id={id}")
    command = ["import"] + ["-var-file=" + _ for _ in var_files] + [addr, id]
    logger.error(str(command))
    with timer(logger, "terraform import"):
        try:
            run_terraform_subprocess(
                command,
                cwd=directory,
                prefix="terraform",
                strip_errors=True,
                timeout=30,
            )
        except TerraformException as e:
            if not exist_ok:
                raise e


def refresh(directory=None, var_files=None):
    var_files = var_files or []

    logger.info(f"terraform refresh directory={directory}")
    command = ["refresh"] + ["-var-file=" + _ for _ in var_files]

    with timer(logger, "terraform refresh"):
        run_terraform_subprocess(command, cwd=directory, prefix="terraform")


def destroy(directory=None, targets=None, var_files=None):
    targets = targets or []
    var_files = var_files or []

    logger.info(f"terraform destroy directory={directory} targets={targets}")
    command = (
        [
            "destroy",
            "-auto-approve",
        ]
        + ["-target=" + _ for _ in targets]
        + ["-var-file=" + _ for _ in var_files]
    )

    with timer(logger, "terraform destroy"):
        run_terraform_subprocess(command, cwd=directory, prefix="terraform")


def rm_local_state(directory=None):
    logger.info(f"rm local state file terraform.tfstate directory={directory}")
    tfstate_path = "terraform.tfstate"
    if directory:
        tfstate_path = os.path.join(directory, tfstate_path)

    if os.path.isfile(tfstate_path):
        os.remove(tfstate_path)


# ========== Terraform JSON ============
@contextlib.contextmanager
def tf_context(filename):
    try:
        tf_clear()
        yield
    finally:
        with open(filename, "w") as f:
            f.write(tf_render())
        tf_clear()


_TF_OBJECTS = {}


def tf_clear():
    global _TF_OBJECTS
    _TF_OBJECTS = {}


def tf_render():
    global _TF_OBJECTS
    return json.dumps(_TF_OBJECTS, indent=4)


def tf_render_objects(terraform_objects):
    return json.dumps(deep_merge(*terraform_objects), indent=4)


def register(f):
    def wrapper(*args, **kwargs):
        global _TF_OBJECTS
        obj = f(*args, **kwargs)
        _TF_OBJECTS = deep_merge(_TF_OBJECTS, obj)
        return obj

    return wrapper


@register
def Terraform(**kwargs):
    return {"terraform": kwargs}


@register
def RequiredProvider(_name, **kwargs):
    return {"terraform": {"required_providers": {_name: kwargs}}}


@register
def Provider(_name, **kwargs):
    return {"provider": {_name: kwargs}}


@register
def TerraformBackend(_name, **kwargs):
    return {"terraform": {"backend": {_name: kwargs}}}


@register
def Variable(_name, **kwargs):
    return {"variable": {_name: kwargs}}


@register
def Data(_resource_type, _name, **kwargs):
    return {"data": {_resource_type: {_name: kwargs}}}


@register
def Resource(_resource_type, _name, **kwargs):
    return {"resource": {_resource_type: {_name: kwargs}}}


@register
def Output(_name, **kwargs):
    return {"output": {_name: kwargs}}
