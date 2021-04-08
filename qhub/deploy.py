import logging
import re
from subprocess import CalledProcessError

from qhub.provider import terraform
from qhub.utils import (
    timer,
    check_cloud_credentials,
    verify_configuration_file_exists,
)
from qhub.provider.dns.cloudflare import update_record

logger = logging.getLogger(__name__)


def deploy_configuration(config, dns_provider, dns_auto_provision, disable_prompt):
    logger.info(f'All qhub endpoints will be under https://{config["domain"]}')

    with timer(logger, "deploying QHub"):
        try:
            guided_install(config, dns_provider, dns_auto_provision, disable_prompt)
        except CalledProcessError as e:
            logger.error(e.output)
            raise e


def guided_install(config, dns_provider, dns_auto_provision, disable_prompt=False):
    # 01 Verify configuration file exists
    verify_configuration_file_exists()

    # 02 Check Environment Variables
    check_cloud_credentials(config)

    # 03 Create terraform backend remote state bucket
    # backwards compatible with `qhub-config.yaml` which
    # don't have `terraform_state` key
    if (config.get("terraform_state", {}).get("type") == "remote") and (
        config.get("provider") != "local"
    ):
        terraform.init(directory="terraform-state")
        terraform.apply(directory="terraform-state")

    # 3.5 kuberentes-alpha provider requires that kubernetes be
    # provisionioned before any "kubernetes_manifests" resources
    terraform.init(directory="infrastructure")
    terraform.apply(
        directory="infrastructure",
        targets=[
            "module.kubernetes",
            "module.kubernetes-initialization",
        ],
    )

    # 04 Create qhub initial state (up to nginx-ingress)
    terraform.init(directory="infrastructure")
    terraform.apply(
        directory="infrastructure",
        targets=[
            "module.kubernetes",
            "module.kubernetes-initialization",
            "module.kubernetes-ingress",
        ],
    )

    cmd_output = terraform.output(directory="infrastructure")
    # This is a bit ugly, but the issue we have at the moment is being unable
    # to parse cmd_output as json on Github Actions.
    ip_matches = re.findall(r'"ip": "(?!string)(.*)"', cmd_output)
    hostname_matches = re.findall(r'"hostname": "(?!string)(.*)"', cmd_output)
    if ip_matches:
        ip_or_hostname = ip_matches[0]
    elif hostname_matches:
        ip_or_hostname = hostname_matches[0]
    else:
        raise ValueError(f"IP Address not found in: {cmd_output}")

    # 05 Update DNS to point to qhub deployment
    if dns_auto_provision and dns_provider == "cloudflare":
        record_name, zone_name = (
            config["domain"].split(".")[:-2],
            config["domain"].split(".")[-2:],
        )
        record_name = ".".join(record_name)
        zone_name = ".".join(zone_name)
        if config["provider"] in {"do", "gcp", "azure"}:
            update_record(zone_name, record_name, "A", ip_or_hostname)
        elif config["provider"] == "aws":
            update_record(zone_name, record_name, "CNAME", ip_or_hostname)
        else:
            logger.info(
                f"Couldn't update the DNS record for cloud provider: {config['provider']}"
            )
    elif not disable_prompt:
        input(
            f"Take IP Address {ip_or_hostname} and update DNS to point to "
            f'"{config["domain"]}" [Press Enter when Complete]'
        )

    # 06 Full deploy QHub
    terraform.apply(directory="infrastructure")
