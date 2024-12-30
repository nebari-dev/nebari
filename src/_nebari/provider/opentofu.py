import contextlib
import io
import json
import logging
import platform
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from _nebari import constants
from _nebari.utils import deep_merge, run_subprocess_cmd, timer

logger = logging.getLogger(__name__)


class OpenTofuException(Exception):
    pass


def deploy(
    directory,
    tofu_init: bool = True,
    tofu_import: bool = False,
    tofu_apply: bool = True,
    tofu_destroy: bool = False,
    input_vars: Dict[str, Any] = {},
    state_imports: List[Any] = [],
):
    """Execute a given directory with OpenTofu infrastructure configuration.

    Parameters:
      directory: directory in which to run tofu operations on

      tofu_init: whether to run `tofu init` default True

      tofu_import: whether to run `tofu import` default
        False for each `state_imports` supplied to function

      tofu_apply: whether to run `tofu apply` default True

      tofu_destroy: whether to run `tofu destroy` default
        False

      input_vars: supply values for "variable" resources within
        terraform module

      state_imports: (addr, id) pairs for iterate through and attempt
        to tofu import
    """
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".tfvars.json"
    ) as f:
        json.dump(input_vars, f.file)
        f.file.flush()

        if tofu_init:
            init(directory)

        if tofu_import:
            for addr, id in state_imports:
                tfimport(
                    addr, id, directory=directory, var_files=[f.name], exist_ok=True
                )

        if tofu_apply:
            apply(directory, var_files=[f.name])

        if tofu_destroy:
            destroy(directory, var_files=[f.name])

        return output(directory)


def download_opentofu_binary(version=constants.OPENTOFU_VERSION):
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

    download_url = f"https://github.com/opentofu/opentofu/releases/download/v{version}/tofu_{version}_{os_mapping[sys.platform]}_{architecture_mapping[platform.machine()]}.zip"

    filename_directory = Path(tempfile.gettempdir()) / "opentofu" / version
    filename_path = filename_directory / "tofu"

    if not filename_path.is_file():
        logger.info(
            f"downloading and extracting opentofu binary from url={download_url} to path={filename_path}"
        )
        with urllib.request.urlopen(download_url) as f:
            bytes_io = io.BytesIO(f.read())
        download_file = zipfile.ZipFile(bytes_io)
        download_file.extract("tofu", filename_directory)

    filename_path.chmod(0o555)
    return filename_path


def run_tofu_subprocess(processargs, **kwargs):
    tofu_path = download_opentofu_binary()
    logger.info(f" tofu at {tofu_path}")
    exit_code, output = run_subprocess_cmd([tofu_path] + processargs, **kwargs)
    if exit_code != 0:
        raise OpenTofuException("OpenTofu returned an error")
    return output


def version():
    tofu_path = download_opentofu_binary()
    logger.info(f"checking opentofu={tofu_path} version")

    version_output = subprocess.check_output([tofu_path, "--version"]).decode("utf-8")
    return re.search(r"(\d+)\.(\d+).(\d+)", version_output).group(0)


def init(directory=None, upgrade=True):
    logger.info(f"tofu init directory={directory}")
    with timer(logger, "tofu init"):
        command = ["init"]
        if upgrade:
            command.append("-upgrade")
        run_tofu_subprocess(command, cwd=directory, prefix="tofu")


def apply(directory=None, targets=None, var_files=None):
    targets = targets or []
    var_files = var_files or []

    logger.info(f"tofu apply directory={directory} targets={targets}")
    command = (
        ["apply", "-auto-approve"]
        + ["-target=" + _ for _ in targets]
        + ["-var-file=" + _ for _ in var_files]
    )
    with timer(logger, "tofu apply"):
        run_tofu_subprocess(command, cwd=directory, prefix="tofu")


def output(directory=None):
    tofu_path = download_opentofu_binary()

    logger.info(f"tofu={tofu_path} output directory={directory}")
    with timer(logger, "tofu output"):
        return json.loads(
            subprocess.check_output(
                [tofu_path, "output", "-json"], cwd=directory
            ).decode("utf8")[:-1]
        )


def tfimport(addr, id, directory=None, var_files=None, exist_ok=False):
    var_files = var_files or []

    logger.info(f"tofu import directory={directory} addr={addr} id={id}")
    command = ["import"] + ["-var-file=" + _ for _ in var_files] + [addr, id]
    logger.error(str(command))
    with timer(logger, "tofu import"):
        try:
            run_tofu_subprocess(
                command,
                cwd=directory,
                prefix="tofu",
                strip_errors=True,
                timeout=30,
            )
        except OpenTofuException as e:
            if not exist_ok:
                raise e


def show(directory=None, tofu_init: bool = True) -> dict:

    if tofu_init:
        init(directory)

    logger.info(f"tofu show directory={directory}")
    command = ["show", "-json"]
    with timer(logger, "tofu show"):
        try:
            output = json.loads(
                run_tofu_subprocess(
                    command,
                    cwd=directory,
                    prefix="tofu",
                    strip_errors=True,
                    capture_output=True,
                )
            )
            return output
        except OpenTofuException as e:
            raise e


def refresh(directory=None, var_files=None):
    var_files = var_files or []

    logger.info(f"tofu refresh directory={directory}")
    command = ["refresh"] + ["-var-file=" + _ for _ in var_files]

    with timer(logger, "tofu refresh"):
        run_tofu_subprocess(command, cwd=directory, prefix="tofu")


def destroy(directory=None, targets=None, var_files=None):
    targets = targets or []
    var_files = var_files or []

    logger.info(f"tofu destroy directory={directory} targets={targets}")
    command = (
        [
            "destroy",
            "-auto-approve",
        ]
        + ["-target=" + _ for _ in targets]
        + ["-var-file=" + _ for _ in var_files]
    )

    with timer(logger, "tofu destroy"):
        run_tofu_subprocess(command, cwd=directory, prefix="tofu")


def rm_local_state(directory=None):
    logger.info(f"rm local state file terraform.tfstate directory={directory}")
    tfstate_path = Path("terraform.tfstate")
    if directory:
        tfstate_path = directory / tfstate_path

    if tfstate_path.is_file():
        tfstate_path.unlink()


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
