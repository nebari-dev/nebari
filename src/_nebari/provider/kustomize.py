import logging
import subprocess
import tempfile
from pathlib import Path

from _nebari import constants
from _nebari.utils import run_subprocess_cmd

logger = logging.getLogger(__name__)


class KustomizeException(Exception):
    pass


def download_kustomize_binary(version=constants.KUSTOMIZE_VERSION) -> Path:
    filename_directory = Path(tempfile.gettempdir()) / "kustomize" / version
    filename_path = filename_directory / "kustomize"

    if not filename_directory.is_dir():
        filename_directory.mkdir(parents=True)

    if not filename_path.is_file():
        logger.info(
            "downloading and extracting kustomize binary version %s to path=%s",
            constants.KUSTOMIZE_VERSION,
            filename_path,
        )
        install_script = subprocess.run(
            [
                "curl",
                "-s",
                "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh",
            ],
            stdout=subprocess.PIPE,
            check=True,
        )
        subprocess.run(
            ["bash", "-s", constants.KUSTOMIZE_VERSION, str(filename_directory)],
            input=install_script.stdout,
            check=True,
        )

    filename_path.chmod(0o555)
    return filename_path


def run_kustomize_subprocess(processargs, **kwargs) -> None:
    kustomize_path = download_kustomize_binary()
    try:
        run_subprocess_cmd(
            [kustomize_path] + processargs, capture_output=True, **kwargs
        )
    except subprocess.CalledProcessError as e:
        raise KustomizeException("Kustomize returned an error: %s" % e.stderr)


def version() -> str:
    kustomize_path = download_kustomize_binary()
    logger.info("checking kustomize=%s version", kustomize_path)

    version_output = subprocess.check_output([kustomize_path, "version"]).decode(
        "utf-8"
    )
    return version_output
