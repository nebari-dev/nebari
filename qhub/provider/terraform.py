import subprocess
import logging
import json

from qhub.utils import timer

logger = logging.getLogger(__name__)


def init(directory=None):
    logger.info(f"terraform init directory={directory}")
    with timer(logger, "terraform init"):
        subprocess.check_output("terraform init", shell=True, cwd=directory)


def apply(directory=None, targets=None):
    targets = targets or []

    logger.info(f"terraform apply directory={directory} targets={targets}")
    with timer(logger, "terraform apply"):
        command = " ".join(
            ["terraform", "apply", "-auto-approve"] + ["-target=" + _ for _ in targets]
        )

        subprocess.check_output(command, shell=True, cwd=directory)


def output(directory=None):
    logger.info(f"terraform output directory={directory}")
    with timer(logger, "terraform output"):
        output = subprocess.check_output(
            "terraform output -json", shell=True, cwd=directory
        ).decode("utf8")
        return json.loads(output)


def destroy(directory=None):
    logger.info(f"terraform destroy directory={directory}")

    with timer(logger, "terraform destroy"):
        command = "terraform destroy -auto-approve"
        subprocess.check_output(command, shell=True, cwd=directory)
