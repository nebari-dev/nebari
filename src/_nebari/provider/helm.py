import logging
import os
import subprocess
import tempfile
from pathlib import Path

from _nebari import constants
from _nebari.utils import run_subprocess_cmd

logger = logging.getLogger(__name__)


class HelmException(Exception):
    pass


def download_helm_binary(version=constants.HELM_VERSION) -> Path:
    filename_directory = Path(tempfile.gettempdir()) / "helm" / version
    filename_path = filename_directory / "helm"

    if not filename_directory.is_dir():
        filename_directory.mkdir(parents=True)

    if not filename_path.is_file():
        logger.info(
            "downloading and extracting Helm binary version %s to path=%s",
            constants.HELM_VERSION,
            filename_path,
        )
        old_path = os.environ.get("PATH")
        new_path = f"{filename_directory}:{old_path}"
        install_script = subprocess.run(
            [
                "curl",
                "-s",
                "https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3",
            ],
            stdout=subprocess.PIPE,
            check=True,
        )
        subprocess.run(
            [
                "bash",
                "-s",
                "--",
                "-v",
                constants.HELM_VERSION,
                "--no-sudo",
            ],
            input=install_script.stdout,
            check=True,
            env={"HELM_INSTALL_DIR": str(filename_directory), "PATH": new_path},
        )

    filename_path.chmod(0o555)
    return filename_path


def run_helm_subprocess(processargs, **kwargs) -> None:
    helm_path = download_helm_binary()
    logger.info("helm at %s", helm_path)
    if run_subprocess_cmd([helm_path] + processargs, **kwargs):
        raise HelmException("Helm returned an error")


def version() -> str:
    helm_path = download_helm_binary()
    logger.info("checking helm=%s version", helm_path)

    version_output = subprocess.check_output([helm_path, "version"]).decode("utf-8")
    return version_output
