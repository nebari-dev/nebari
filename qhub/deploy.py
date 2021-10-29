import logging
import os
import re
import socket

from qhub.provider import terraform
from qhub.utils import timer, check_cloud_credentials, QHubError
from qhub.provider.dns.cloudflare import update_record
from qhub.state import terraform_state_sync
from qhub.console import console

logger = logging.getLogger(__name__)


def deploy_configuration(
    config,
    dns_provider,
    dns_auto_provision,
    disable_prompt=False,
    skip_remote_state_provision=False,
    verbose=True,
):
    # 01 Check Environment Variables
    check_cloud_credentials(config)
    console.print("Validated QHub environment variables for provider")

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
        with timer(
            "Creating terraform remote state",
            "Created terraform remote state",
            verbose=verbose,
        ):
            terraform_state_sync(config)

    # 3 kubernetes-alpha provider requires that kubernetes be
    # provisionioned before any "kubernetes_manifests" resources
    with timer(
        "Deploying QHub infrastructure (cloud, managed kubernetes)",
        "Deployed QHub infrastructure (cloud, managed kubernetes)",
        verbose=verbose,
    ):
        terraform.init(directory="infrastructure")
        terraform.apply(
            directory="infrastructure",
            targets=[
                "module.kubernetes",
                "module.kubernetes-initialization",
            ],
        )

    # 04 Create qhub initial state (up to nginx-ingress)
    with timer(
        "Deploying QHub core components (namespace, ingress, authentication, monitoring)",
        "Deployed QHub core components (namespace, ingress, authentication, monitoring)",
        verbose=verbose,
    ):
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
    with timer("Deploying QHub", "Deployed QHub", verbose=verbose):
        terraform.apply(directory="infrastructure")

    check_qhub_address(ip_or_hostname, config["domain"])

    console.rule("Successful QHub Deployment")
    console.print(
        f'Visit https://{config["domain"]} to access your QHub Cluster\n'
        "Administrator documentation: https://docs.qhub.dev/en/stable/source/admin_guide/\n"
        "End user documentation: https://docs.qhub.dev/en/stable/source/user_guide/"
    )


def check_qhub_address(ip_or_hostname: str, domain: str):
    """Check that the QHub domain points to the load balancer IP address or CNAME

    This check can be flaky in the sense that DNS takes time to propagate.
    """
    try:
        resolved_domain_ip = socket.gethostbyname(domain)
    except socket.gaierror:
        resolved_domain_ip = None

    resolved_load_balancer_ip = socket.gethostbyname(ip_or_hostname)

    if resolved_domain_ip is None:
        console.print(
            f'Domain "{domain}" currently does not resolve\n'
            f"Make sure to point DNS to {ip_or_hostname}\n"
            "See https://docs.qhub.dev/en/stable/source/installation/setup.html#domain-registry\n"
            , style="orange1")
    elif resolved_load_balancer_ip != resolved_domain_ip:
        console.print(
            f'Domain "{domain}" is set but does not resolve to "{ip_or_hostname}"\n'
            f'Currently resolving "{domain}" -> "{resolved_domain_ip}" and "{ip_or_hostname}" -> "{resolved_load_balancer_ip}"\n'
            'If this is a production deployment this most likely an error\n'
            , style="orange1")
    else:
        console.print(f'Domain "{domain}" properly resolves to "{ip_or_hostname}"')


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
