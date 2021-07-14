import logging
import os
import re
from subprocess import CalledProcessError

from qhub.provider import terraform
from qhub.utils import timer, check_cloud_credentials
from qhub.provider.dns.cloudflare import update_record
from qhub.state import terraform_state_sync

logger = logging.getLogger(__name__)


def deploy_configuration(
    config,
    dns_provider,
    dns_auto_provision,
    disable_prompt,
    skip_remote_state_provision,
):
    logger.info(f'All qhub endpoints will be under https://{config["domain"]}')

    with timer(logger, "deploying QHub"):
        try:
            guided_install(
                config,
                dns_provider,
                dns_auto_provision,
                disable_prompt,
                skip_remote_state_provision,
            )
        except CalledProcessError as e:
            logger.error(e.output)
            raise e


def guided_install(
    config,
    dns_provider,
    dns_auto_provision,
    disable_prompt=False,
    skip_remote_state_provision=False,
):
    # 01 Check Environment Variables
    check_cloud_credentials(config)
    # Check that secrets required for terraform
    # variables are set as required
    check_secrets(config)

    # 02 Create terraform backend remote state bucket
    # backwards compatible with `qhub-config.yaml` which
    # don't have `terraform_state` key
    if (
        (not skip_remote_state_provision)
        and (config.get("terraform_state", {}).get("type", "") == "remote")
        and (config.get("provider") != "local")
    ):
        terraform_state_sync(config)

    # 3 kuberentes-alpha provider requires that kubernetes be
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
    ip_matches = re.findall(r'"ip": "(?!string)(.+)"', cmd_output)
    hostname_matches = re.findall(r'"hostname": "(?!string)(.+)"', cmd_output)
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
            if config.get("clearml", {}).get("enabled"):
                add_clearml_dns(zone_name, record_name, "A", ip_or_hostname)
        elif config["provider"] == "aws":
            update_record(zone_name, record_name, "CNAME", ip_or_hostname)
            if config.get("clearml", {}).get("enabled"):
                add_clearml_dns(zone_name, record_name, "CNAME", ip_or_hostname)
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


def add_clearml_dns(zone_name, record_name, record_type, ip_or_hostname):
    logger.info(f"Setting DNS record for ClearML for record: {record_name}")
    dns_records = [
        f"app.clearml.{record_name}",
        f"api.clearml.{record_name}",
        f"files.clearml.{record_name}",
    ]

    for dns_record in dns_records:
        update_record(zone_name, dns_record, record_type, ip_or_hostname)


def check_secrets(config):
    """
    Checks that the appropriate variables are set based on the current config.
    These variables are prefixed with TF_VAR_ and are used to populate the
    corresponding variables in the terraform deployment. e.g.
    TF_VAR_prefect_token sets the prefect_token variable in Terraform. These
    values are set in the terraform state but are not leaked when the
    terraform render occurs.
    """

    missing_env_vars = []

    # Check prefect integration set up.
    if "prefect" in config and config["prefect"]["enabled"]:
        var = "TF_VAR_prefect_token"
        if var not in os.environ:
            missing_env_vars.append(var)

    if missing_env_vars:
        raise EnvironmentError(
            "Some environment variables used to propagate secrets to the "
            "terraform deployment were not set. Please set these before "
            f"continuing: {', '.join(missing_env_vars)}"
        )
