import logging
import os
import subprocess
import textwrap

from qhub.provider import terraform
from qhub.provider.dns.cloudflare import update_record
from qhub.stages import checks, input_vars, state_imports
from qhub.utils import (
    check_cloud_credentials,
    keycloak_provider_context,
    kubernetes_provider_context,
    timer,
)

logger = logging.getLogger(__name__)


def provision_01_terraform_state(stage_outputs, config):
    directory = "stages/01-terraform-state"

    if config["provider"] in {"existing", "local"}:
        stage_outputs[directory] = {}
    else:
        stage_outputs[directory] = terraform.deploy(
            terraform_import=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars=input_vars.stage_01_terraform_state(stage_outputs, config),
            state_imports=state_imports.stage_01_terraform_state(stage_outputs, config),
        )


def provision_02_infrastructure(stage_outputs, config, disable_checks=False):
    """Generalized method to provision infrastructure

    After successful deployment the following properties are set on
    `stage_outputs[directory]`.
      - `kubernetes_credentials` which are sufficient credentials to
        connect with the kubernetes provider
      - `kubeconfig_filename` which is a path to a kubeconfig that can
        be used to connect to a kubernetes cluster
      - at least one node running such that resources in the
        node_group.general can be scheduled

    At a high level this stage is expected to provision a kubernetes
    cluster on a given provider.
    """
    directory = "stages/02-infrastructure"

    stage_outputs[directory] = terraform.deploy(
        os.path.join(directory, config["provider"]),
        input_vars=input_vars.stage_02_infrastructure(stage_outputs, config),
    )

    if not disable_checks:
        checks.stage_02_infrastructure(stage_outputs, config)


def provision_03_kubernetes_initialize(stage_outputs, config, disable_checks=False):
    directory = "stages/03-kubernetes-initialize"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars=input_vars.stage_03_kubernetes_initialize(stage_outputs, config),
    )

    if not disable_checks:
        checks.stage_03_kubernetes_initialize(stage_outputs, config)


def provision_04_kubernetes_ingress(stage_outputs, config, disable_checks=False):
    directory = "stages/04-kubernetes-ingress"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars=input_vars.stage_04_kubernetes_ingress(stage_outputs, config),
    )

    if not disable_checks:
        checks.stage_04_kubernetes_ingress(stage_outputs, config)


def add_clearml_dns(zone_name, record_name, record_type, ip_or_hostname):
    dns_records = [
        f"app.clearml.{record_name}",
        f"api.clearml.{record_name}",
        f"files.clearml.{record_name}",
    ]

    for dns_record in dns_records:
        update_record(zone_name, dns_record, record_type, ip_or_hostname)


def provision_ingress_dns(
    stage_outputs,
    config,
    dns_provider: str,
    dns_auto_provision: bool,
    disable_prompt: bool = True,
    disable_checks: bool = False,
):
    directory = "stages/04-kubernetes-ingress"

    ip_or_name = stage_outputs[directory]["load_balancer_address"]["value"]
    ip_or_hostname = ip_or_name["hostname"] or ip_or_name["ip"]

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

    if not disable_checks:
        checks.check_ingress_dns(stage_outputs, config, disable_prompt)


def provision_05_kubernetes_keycloak(stage_outputs, config, disable_checks=False):
    directory = "stages/05-kubernetes-keycloak"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars=input_vars.stage_05_kubernetes_keycloak(stage_outputs, config),
    )

    if not disable_checks:
        checks.stage_05_kubernetes_keycloak(stage_outputs, config)


def provision_06_kubernetes_keycloak_configuration(
    stage_outputs, config, disable_checks=False
):
    directory = "stages/06-kubernetes-keycloak-configuration"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars=input_vars.stage_06_kubernetes_keycloak_configuration(
            stage_outputs, config
        ),
    )

    if not disable_checks:
        checks.stage_06_kubernetes_keycloak_configuration(stage_outputs, config)


def provision_07_kubernetes_services(stage_outputs, config, disable_checks=False):
    directory = "stages/07-kubernetes-services"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars=input_vars.stage_07_kubernetes_services(stage_outputs, config),
    )

    if not disable_checks:
        checks.stage_07_kubernetes_services(stage_outputs, config)


def provision_08_qhub_tf_extensions(stage_outputs, config, disable_checks=False):
    directory = "stages/08-qhub-tf-extensions"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars=input_vars.stage_08_qhub_tf_extensions(stage_outputs, config),
    )

    if not disable_checks:
        pass


def guided_install(
    config,
    dns_provider,
    dns_auto_provision,
    disable_prompt=False,
    disable_checks=False,
    skip_remote_state_provision=False,
):
    # 01 Check Environment Variables
    check_cloud_credentials(config)

    stage_outputs = {}
    if (
        config["provider"] not in {"existing", "local"}
        and config["terraform_state"]["type"] == "remote"
    ):
        if skip_remote_state_provision:
            print("Skipping remote state provision")
        else:
            provision_01_terraform_state(stage_outputs, config)

    provision_02_infrastructure(stage_outputs, config, disable_checks)

    with kubernetes_provider_context(
        stage_outputs["stages/02-infrastructure"]["kubernetes_credentials"]["value"]
    ):
        provision_03_kubernetes_initialize(stage_outputs, config, disable_checks)
        provision_04_kubernetes_ingress(stage_outputs, config, disable_checks)
        provision_ingress_dns(
            stage_outputs,
            config,
            dns_provider=dns_provider,
            dns_auto_provision=dns_auto_provision,
            disable_prompt=disable_prompt,
            disable_checks=disable_checks,
        )
        provision_05_kubernetes_keycloak(stage_outputs, config, disable_checks)

        with keycloak_provider_context(
            stage_outputs["stages/05-kubernetes-keycloak"]["keycloak_credentials"][
                "value"
            ]
        ):
            provision_06_kubernetes_keycloak_configuration(
                stage_outputs, config, disable_checks
            )
            provision_07_kubernetes_services(stage_outputs, config, disable_checks)
            provision_08_qhub_tf_extensions(stage_outputs, config, disable_checks)

            print("QHub deployed successfully")

    print("Services:")
    for service_name, service in stage_outputs["stages/07-kubernetes-services"][
        "service_urls"
    ]["value"].items():
        print(f" - {service_name} -> {service['url']}")

    print(
        f"Kubernetes kubeconfig located at file://{stage_outputs['stages/02-infrastructure']['kubeconfig_filename']['value']}"
    )
    username = "root"
    password = (
        config.get("security", {}).get("keycloak", {}).get("initial_root_password", "")
    )
    if password:
        print(f"Kubecloak master realm username={username} password={password}")

    print(
        "Additional administration docs can be found at https://docs.qhub.dev/en/stable/source/admin_guide/"
    )


def deploy_configuration(
    config,
    dns_provider,
    dns_auto_provision,
    disable_prompt,
    disable_checks,
    skip_remote_state_provision,
):
    if config.get("prevent_deploy", False):
        # Note if we used the Pydantic model properly, we might get that qhub_config.prevent_deploy always exists but defaults to False
        raise ValueError(
            textwrap.dedent(
                """
        Deployment prevented due to the prevent_deploy setting in your qhub-config.yaml file.
        You could remove that field to deploy your QHub, but please do NOT do so without fully understanding why that value was set in the first place.

        It may have been set during an upgrade of your qhub-config.yaml file because we do not believe it is safe to redeploy the new
        version of QHub without having a full backup of your system ready to restore. It may be known that an in-situ upgrade is impossible
        and that redeployment will tear down your existing infrastructure before creating an entirely new QHub without your old data.

        PLEASE get in touch with Quansight at https://github.com/Quansight/qhub for assistance in proceeding.
        Your data may be at risk without our guidance.
        """
            )
        )

    logger.info(f'All qhub endpoints will be under https://{config["domain"]}')

    if disable_checks:
        logger.warning(
            "The validation checks at the end of each stage have been disabled"
        )

    with timer(logger, "deploying QHub"):
        try:
            guided_install(
                config,
                dns_provider,
                dns_auto_provision,
                disable_prompt,
                disable_checks,
                skip_remote_state_provision,
            )
        except subprocess.CalledProcessError as e:
            logger.error(e.output)
            raise e
