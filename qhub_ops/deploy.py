import yaml
import pathlib
import logging
import re

from qhub_ops.render import render_default_template
from qhub_ops.provider.oauth import auth0
from qhub_ops.provider.dns import cloudflare
from qhub_ops.provider import terraform
from qhub_ops.utils import timer

logger = logging.getLogger(__name__)


def deploy_configuration(config):
    logger.info(f'All qhub endpoints will be under *.{config["domain"]}')

    jupyterhub_endpoint = f'jupyter.{config["domain"]}'
    if (
        "client_id" not in config["authentication"]["config"]
        or "client_secret" not in config["authentication"]["config"]
    ):
        logger.info(
            "client_id and client_secret were not specified - dynamically creating oauth client"
        )
        with timer(logger, "creating oauth client"):
            config["authentication"]["config"] = auth0.create_client(
                jupyterhub_endpoint
            )

    with timer(logger, "rendering template"):
        tmp_config = pathlib.Path("./config.yaml")
        with tmp_config.open("w") as f:
            yaml.dump(config, f)

        render_default_template(".", tmp_config)

    infrastructure_dir = pathlib.Path(config["project_name"]) / "infrastructure"

    terraform.init(str(infrastructure_dir))

    # ========= boostrap infrastructure ========
    terraform.apply(
        str(infrastructure_dir),
        targets=[
            "module.kubernetes",
            "module.kubernetes-initialization",
            "module.kubernetes-ingress",
        ],
    )

    # ============= update dns ================
    output = terraform.output(str(infrastructure_dir))
    for key in output:
        if key.startswith("ingress"):
            endpoint = f'{key.split("_")[1]}.{config["domain"]}'
            address = output[key]["value"]
            if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", address):
                cloudflare.update_record("qhub.dev", endpoint, "A", address)
            else:
                cloudflare.update_record("qhub.dev", endpoint, "CNAME", address)

    # ======= apply entire infrastructure ========
    terraform.apply(str(infrastructure_dir))
