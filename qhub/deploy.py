import logging
import os
import re
import contextlib
from subprocess import CalledProcessError
from typing import List, Dict
import tempfile

from qhub.provider import terraform
from qhub.utils import timer, check_cloud_credentials, modified_environ, split_docker_image_name
from qhub.provider.dns.cloudflare import update_record
from qhub.render.terraform import QHubKubernetesProvider, QHubTerraformState, QHubGCPProvider, QHubAWSProvider
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
def kubernetes_provider_context(kubernetes_credentials : Dict[str, str]):
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

    credentials = {credential_mapping[k]: v for k,v in kubernetes_credentials.items() if v is not None}
    with modified_environ(**credentials):
        yield


@contextlib.contextmanager
def keycloak_provider_context(keycloak_credentials : Dict[str, str]):
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


def calculate_note_groups(config):
    if config['provider'] == 'aws':
        return {group: {"key": "eks.amazonaws.com/nodegroup", "value": group} for group in ['general', 'user', 'worker']}
    elif config['provider'] == 'gcp':
        return {group: {"key": "cloud.google.com/gke-nodepool", "value": group} for group in ['general', 'user', 'worker']}
    elif config['provider'] == 'azure':
        return {group: {"key": "azure-node-pool", "value": group} for group in ['general', 'user', 'worker']}
    elif config['provider'] == 'do':
        return {group: {"key": "doks.digitalocean.com/node-pool", "value": group} for group in ['general', 'user', 'worker']}
    else:
        return config['local']['node_selectors']


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

    if config['provider'] == "local":
        stage_outputs['stages/02-infrastructure'] = terraform.deploy(
            os.path.join("stages/02-infrastructure", config['provider']),
            input_vars={
                "kube_context": config['local'].get('kube_context')
            })
    elif config['provider'] == 'do':
        stage_outputs['stages/01-terraform-state'] = terraform.deploy(
            os.path.join("stages/01-terraform-state", config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
                'region': config['digital_ocean']['region']
            })

        stage_outputs['stages/02-infrastructure'] = terraform.deploy(
            os.path.join("stages/02-infrastructure", config['provider']),
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                'region': config['digital_ocean']['region'],
                'kubernetes_version': config['digital_ocean']['kubernetes_version'],
                'node_groups': config['digital_ocean']['node_groups'],
                'kubeconfig_filename': os.path.join(tempfile.gettempdir(), 'QHUB_KUBECONFIG')
            },
            terraform_objects=[
                QHubTerraformState('02-infrastructure', config),
            ])
    elif config['provider'] == 'gcp':
        stage_outputs['stages/01-terraform-state'] = terraform.deploy(
            os.path.join("stages/01-terraform-state", config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
                'region': config['google_cloud_platform']['region']
            },
            terraform_objects=[
                QHubGCPProvider(config),
            ])

        stage_outputs['stages/02-infrastructure'] = terraform.deploy(
            os.path.join("stages/02-infrastructure", config['provider']),
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                'region': config['google_cloud_platform']['region'],
                'project_id': config['google_cloud_platform']['project'],
                'node_groups': [{'name': key, 'min_size': value['min_nodes'], 'max_size': value['max_nodes'], **value} for key, value in config['google_cloud_platform']['node_groups'].items()],
                'kubeconfig_filename': os.path.join(tempfile.gettempdir(), 'QHUB_KUBECONFIG')
            },
            terraform_objects=[
                QHubGCPProvider(config),
                QHubTerraformState('02-infrastructure', config),
            ])
    elif config['provider'] == 'azure':
        stage_outputs['stages/01-terraform-state'] = terraform.deploy(
            os.path.join("stages/01-terraform-state", config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
                'region': config['azure']['region'],
                'storage_account_postfix': config['azure']['storage_account_postfix'],
            })

        stage_outputs['stages/02-infrastructure'] = terraform.deploy(
            os.path.join("stages/02-infrastructure", config['provider']),
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                'region': config['azure']['region'],
                'kubernetes_version': config['azure']['kubernetes_version'],
                'node_groups': config['azure']['node_groups'],
                'kubeconfig_filename': os.path.join(tempfile.gettempdir(), 'QHUB_KUBECONFIG')
            },
            terraform_objects=[
                QHubTerraformState('02-infrastructure', config),
            ])
    elif config['provider'] == 'aws':
        stage_outputs['stages/01-terraform-state'] = terraform.deploy(
            os.path.join("stages/01-terraform-state", config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
            },
            terraform_objects=[
                QHubAWSProvider(config),
            ])

        stage_outputs['stages/02-infrastructure'] = terraform.deploy(
            os.path.join("stages/02-infrastructure", config['provider']),
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                'node_groups': [{'name': key, 'min_size': value['min_nodes'], 'desired_size': value['min_nodes'], 'max_size': value['max_nodes'], 'gpu': value.get('gpu', False), 'instance_type': value['instance']} for key, value in config['amazon_web_services']['node_groups'].items()],
                'kubeconfig_filename': os.path.join(tempfile.gettempdir(), 'QHUB_KUBECONFIG')
            },
            terraform_objects=[
                QHubAWSProvider(config),
                QHubTerraformState('02-infrastructure', config),
            ])

    with kubernetes_provider_context(
            stage_outputs['stages/02-infrastructure']['kubernetes_credentials']['value']):
        stage_outputs["stages/03-kubernetes-initialize"] = terraform.deploy(
            directory="stages/03-kubernetes-initialize",
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                'qhub_config': config,
                'external_container_reg': config.get('external_container_reg', {'enabled': False})
            },
            terraform_objects=[
                QHubTerraformState('03-kubernetes-initialize', config),
                QHubKubernetesProvider(config),
            ])

        stage_outputs["stages/04-kubernetes-ingress"] = terraform.deploy(
            directory="stages/04-kubernetes-ingress",
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                "node_groups": calculate_note_groups(config),
                "enable-certificates": (config['certificate']['type'] == 'lets-encrypt'),
                "acme-email": config['certificate'].get('acme_email'),
                "acme-server": config['certificate'].get('acme_server'),
                "certificate-secret-name": config['certificate']['secret_name'] if config['certificate']['type'] == 'lets-encrypt' else None,
            },
            terraform_objects=[
                QHubTerraformState('04-kubernetes-ingress', config),
                QHubKubernetesProvider(config),
            ])

        stage_outputs["stages/05-kubernetes-keycloak"] = terraform.deploy(
            directory="stages/05-kubernetes-keycloak",
            input_vars={
                'name': config['project_name'],
                'environment': config['namespace'],
                'endpoint': config['domain'],
                'initial-root-password': config['security']['keycloak']['initial_root_password']
            },
            terraform_objects=[
                QHubTerraformState('05-kubernetes-keycloak', config),
                QHubKubernetesProvider(config),
            ])

        with keycloak_provider_context(
                stage_outputs['stages/05-kubernetes-keycloak']['keycloak_credentials']['value']):
            stage_outputs["stages/06-kubernetes-keycloak-configuration"] = terraform.deploy(
                directory='stages/06-kubernetes-keycloak-configuration',
                input_vars={
                    'realm': f"qhub-{config['project_name']}",
                    'authentication': config['security']['authentication']
                },
                terraform_objects=[
                    QHubTerraformState('06-kubernetes-keycloak-configuration', config),
                ])


            stage_outputs["stages/07-kubernetes-services"] = terraform.deploy(
                directory="stages/07-kubernetes-services", input_vars={
                    "name": config['project_name'],
                    "environment": config['namespace'],
                    "endpoint": config['domain'],
                    "realm_id": stage_outputs['stages/06-kubernetes-keycloak-configuration']['realm_id']['value'],
                    "node_groups": calculate_note_groups(config),
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
                    # dask-gateway
                    "dask-gateway-image": split_docker_image_name(config['default_images']['dask_gateway']),
                    "dask-worker-image": split_docker_image_name(config['default_images']['dask_worker']),
                    "dask-gateway-profiles": config['profiles']['dask_worker'],
                    # monitoring
                    "monitoring-enabled": config['monitoring']['enabled'],
                    # prefect
                    "prefect-enabled": config.get('prefect', {}).get('enabled', False),
                    "prefect-token": config.get('prefect', {}).get('token', ''),
                    "prefect-image": config.get('prefect', {}).get('image', ""),
                    "prefect-overrides": config.get('prefect', {}).get('overrides', {}),
                    # clearml
                    "clearml-enabled": config.get('clearml', {}).get('enabled', False),
                    "clearml-enable-forwardauth": config.get('clearml', {}).get('enable_forward_auth', False),
                },
                terraform_objects=[
                    QHubTerraformState('07-kubernetes-services', config),
                    QHubKubernetesProvider(config),
                ])


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
