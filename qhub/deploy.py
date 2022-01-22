import logging
import os
import re
import contextlib
from subprocess import CalledProcessError

from qhub.provider import terraform
from qhub.utils import timer, check_cloud_credentials, modified_environ, split_docker_image_name
from qhub.provider.dns.cloudflare import update_record
from qhub.state import terraform_state_sync

logger = logging.getLogger(__name__)


def deploy_configuration(
    config,
    dns_provider,
    dns_auto_provision,
    disable_prompt,
    skip_remote_state_provision,
    full_only,
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
                full_only,
            )
        except CalledProcessError as e:
            logger.error(e.output)
            raise e


@contextlib.contextmanager
def kubernetes_provider_context(kubernetes_credentials):
    credential_mapping = {
        'config_path': 'KUBE_CONFIG_PATH',
        'config_context': 'KUBE_CTX',
        'username': 'KUBE_USER',
        'password': 'KUBE_PASSWORD',
        'client_certificate': 'KUBE_CLIENT_CERT_DATA',
        'client_key': 'KUBE_CLIENT_KEY_DATA',
        'cluster_ca_certificate': 'KUBE_CLUSTER_CA_CERT_DATA',
        'host': 'KUBE_HOST',
        'token': 'KUBE_TOKEN',
    }

    credentials = {credential_mapping[k]: v for k,v in kubernetes_credentials.items()}
    with modified_environ(**credentials):
        yield


@contextlib.contextmanager
def keycloak_provider_context(keycloak_credentials):
    credential_mapping = {
        'client_id': 'KEYCLOAK_CLIENT_ID',
        'url': 'KEYCLOAK_URL',
        'username': 'KEYCLOAK_USER',
        'password': 'KEYCLOAK_PASSWORD',
        'realm': 'KEYCLOAK_REALM',
    }

    credentials = {credential_mapping[k]: v for k,v in keycloak_credentials.items()}
    with modified_environ(**credentials):
        yield



def guided_install(
    config,
    dns_provider,
    dns_auto_provision,
    disable_prompt=False,
    skip_remote_state_provision=False,
    full_only=False,
):
    # 01 Check Environment Variables
    check_cloud_credentials(config)
    # Check that secrets required for terraform
    # variables are set as required
    check_secrets(config)

    stage_outputs = {}

    for stage in [
        "stages/01-terraform-state",
        "stages/02-infrastructure",
    ]:
        logger.info(f"Running Terraform Stage={stage}")
        stage_outputs[stage] = terraform.deploy(stage)

    with kubernetes_provider_context(
            stage_outputs['stages/02-infrastructure']['kubernetes_credentials']['value']):
        stage_outputs["stages/03-kubernetes-initialize"] = terraform.deploy(
            directory="stages/03-kubernetes-initialize",
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
            })

        stage_outputs["stages/04-kubernetes-ingress"] = terraform.deploy(
            directory="stages/04-kubernetes-ingress",
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
            })

        stage_outputs["stages/05-kubernetes-keycloak"] = terraform.deploy(
            directory="stages/05-kubernetes-keycloak",
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                'endpoint': config['domain'],
                'initial-root-password': config['security']['keycloak']['initial_root_password']
            })

        with keycloak_provider_context(
                stage_outputs['stages/05-kubernetes-keycloak']['keycloak_credentials']['value']):
            stage_outputs["stages/06-kubernetes-keycloak-configuration"] = terraform.deploy(
                directory='stages/06-kubernetes-keycloak-configuration',
                input_vars={
                    'realm': f"qhub-{config['project_name']}",
                    'authentication': config['security']['authentication']
                })

            stage_outputs["stages/07-kubernetes-services"] = terraform.deploy(
                directory="stages/07-kubernetes-services", input_vars={
                    "name": config['project_name'],
                    "environment": config['namespace'],
                    "endpoint": config['domain'],
                    "realm_id": stage_outputs['stages/06-kubernetes-keycloak-configuration']['realm_id']['value'],
                    # conda-store
                    "conda-store-environments": config['environments'],
                    "conda-store-storage": config['storage']['conda_store'],
                    "conda-store-image": split_docker_image_name(config['default_images']['conda_store']),
                    # jupyterhub
                    "cdsdashboards": config['cdsdashboards'],
                    "jupyterhub-theme": config['theme']['jupyterhub'],
                    "jupyterhub-image": split_docker_image_name(config['default_images']['jupyterhub']),
                    "jupyterhub-shared-storage": config['storage']['shared_filesystem'],
                    "jupyterlab-profiles": config['profiles']['jupyterlab'],
                    "jupyterlab-image": split_docker_image_name(config['default_images']['jupyterlab']),
                })

    import pprint
    pprint.pprint(stage_outputs)

    pprint.pprint(config)


    #     cmd_output = terraform.output(directory="infrastructure")
    #     # This is a bit ugly, but the issue we have at the moment is being unable
    #     # to parse cmd_output as json on Github Actions.
    #     ip_matches = re.findall(r'"ip": "(?!string)(.+)"', cmd_output)
    #     hostname_matches = re.findall(r'"hostname": "(?!string)(.+)"', cmd_output)
    #     if ip_matches:
    #         ip_or_hostname = ip_matches[0]
    #     elif hostname_matches:
    #         ip_or_hostname = hostname_matches[0]
    #     else:
    #         raise ValueError(f"IP Address not found in: {cmd_output}")

    #     # 05 Update DNS to point to qhub deployment
    #     if dns_auto_provision and dns_provider == "cloudflare":
    #         record_name, zone_name = (
    #             config["domain"].split(".")[:-2],
    #             config["domain"].split(".")[-2:],
    #         )
    #         record_name = ".".join(record_name)
    #         zone_name = ".".join(zone_name)
    #         if config["provider"] in {"do", "gcp", "azure"}:
    #             update_record(zone_name, record_name, "A", ip_or_hostname)
    #             if config.get("clearml", {}).get("enabled"):
    #                 add_clearml_dns(zone_name, record_name, "A", ip_or_hostname)
    #         elif config["provider"] == "aws":
    #             update_record(zone_name, record_name, "CNAME", ip_or_hostname)
    #             if config.get("clearml", {}).get("enabled"):
    #                 add_clearml_dns(zone_name, record_name, "CNAME", ip_or_hostname)
    #         else:
    #             logger.info(
    #                 f"Couldn't update the DNS record for cloud provider: {config['provider']}"
    #             )
    #     elif not disable_prompt:
    #         input(
    #             f"Take IP Address {ip_or_hostname} and update DNS to point to "
    #             f'"{config["domain"]}" [Press Enter when Complete]'
    #         )

    #     # Now Keycloak Helm chart (External Docker Registry before that if we need one)
    #     targets = ["module.external-container-reg", "module.kubernetes-keycloak-helm"]
    #     logger.info(f"Running Terraform Stage: {targets}")
    #     terraform.apply(
    #         directory="infrastructure",
    #         targets=targets,
    #     )

    #     # Now Keycloak realm and config
    #     targets = ["module.kubernetes-keycloak-config"]
    #     logger.info(f"Running Terraform Stage: {targets}")
    #     terraform.apply(
    #         directory="infrastructure",
    #         targets=targets,
    #     )

    # # Full deploy QHub
    # logger.info("Running Terraform Stage: FULL")
    # terraform.apply(directory="infrastructure")


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
    corresponding variables in the terraform deployment. for example
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
