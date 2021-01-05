import logging
import re
from subprocess import check_output, run

from qhub.utils import (
    timer,
    change_directory,
    check_cloud_credentials,
    verify_configuration_file_exists,
    check_terraform,
)
from qhub.provider.dns.cloudflare import update_record

logger = logging.getLogger(__name__)


def deploy_configuration(config, dns_provider, dns_auto_provision, disable_prompt):
    logger.info(f'All qhub endpoints will be under *.{config["domain"]}')

    with timer(logger, "deploying QHub"):
        guided_install(config, dns_provider, dns_auto_provision, disable_prompt)


def guided_install(config, dns_provider, dns_auto_provision, disable_prompt=False):
    # 01 Verify configuration file exists
    verify_configuration_file_exists()

    # 02 Check terraform
    check_terraform()

    # 03 Check Environment Variables
    check_cloud_credentials(config)

    # 04 Check that oauth settings are set
    if not disable_prompt:
        input(
            'Ensure that oauth settings are in configuration [Press "Enter" to continue]'
        )

    # 05 Create terraform backend remote state bucket
    with change_directory("terraform-state"):
        run(["terraform", "init"])
        run(["terraform", "apply", "-auto-approve"])

    # 06 Create qhub initial state (up to nginx-ingress)
    with change_directory("infrastructure"):
        run(["terraform", "init"])
        run(
            [
                "terraform",
                "apply",
                "-auto-approve",
                "-target=module.kubernetes",
                "-target=module.kubernetes-initialization",
                "-target=module.kubernetes-ingress",
            ]
        )
        cmd_output = check_output(["terraform", "output", "--json"])
        # This is a bit ugly, but the issue we have at the moment is being unable
        # to parse cmd_output as json on Github Actions.
        ip_matches = re.findall(rb'"ip": "(?!string)(.*)"', cmd_output)
        if ip_matches:
            ip = ip_matches[0].decode()
        else:
            raise ValueError(f"IP Address not found in: {cmd_output}")
    # 07 Update DNS to point to qhub deployment
    if dns_auto_provision and dns_provider == "cloudflare":
        record_name, zone_name = (
            config["domain"].split(".")[:-2],
            config["domain"].split(".")[-2:],
        )
        record_name = f'jupyter.{".".join(record_name)}'
        zone_name = ".".join(zone_name)
        if config["provider"] in {"do", "gcp"}:
            update_record(zone_name, record_name, "A", ip)
    else:
        input(
            f'Take IP Address {ip} and update DNS to point to "jupyter.{config["domain"]}" [Press Enter when Complete]'
        )

    # 08 Full deploy QHub
    with change_directory("infrastructure"):
        run(["terraform", "apply", "-auto-approve"])
