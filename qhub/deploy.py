import logging
import os
import re
import sys
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


def provision_01_terraform_state(stage_outputs, config):
    directory = 'stages/01-terraform-state'

    if config['provider'] == "local":
        stage_outputs[directory] = {}
    elif config['provider'] == 'do':
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
                'region': config['digital_ocean']['region']
            })
    elif config['provider'] == 'gcp':
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
                'region': config['google_cloud_platform']['region']
            },
            terraform_objects=[
                QHubGCPProvider(config),
            ])
    elif config['provider'] == 'azure':
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
                'region': config['azure']['region'],
                'storage_account_postfix': config['azure']['storage_account_postfix'],
            })
    elif config['provider'] == 'aws':
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config['provider']),
            input_vars={
                'name': config['project_name'],
                'namespace': config['namespace'],
            },
            terraform_objects=[
                QHubAWSProvider(config),
            ])
    else:
        raise NotImplementedError(f'provider {config["provider"]} not implemented for directory={directory}')


def provision_02_infrastructure(stage_outputs, config, check=True):
    """Generalized method to provision infrastructure

    After succesfull deployment the following properties are set on
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
    directory = 'stages/02-infrastructure'

    if config['provider'] == "local":
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config['provider']),
            input_vars={
                "kube_context": config['local'].get('kube_context')
            })
    elif config['provider'] == 'do':
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config['provider']),
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
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config['provider']),
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
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config['provider']),
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
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config['provider']),
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
    else:
        raise NotImplementedError(f'provider {config["provider"]} not implemented for directory={directory}')

    if check:
        check_02_infrastructure(stage_outputs, config)


def check_02_infrastructure(stage_outputs, qhub_config):
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    directory = "stages/02-infrastructure"
    config.load_kube_config(
        config_file=stage_outputs['stages/02-infrastructure']['kubeconfig_filename']['value'])

    try:
        api_instance = client.CoreV1Api()
        result = api_instance.list_node()
    except ApiException:
        print(f'ERROR: After stage directory={directory} unable to connect to kubernetes cluster')
        sys.exit(1)

    if len(result.items) < 1:
        print(f"ERROR: After stage directory={directory} no nodes provisioned within kubernetes cluster")
        sys.exit(1)

    print(f'After stage directory={directory} kubernetes cluster successfully provisioned')


def provision_03_kubernetes_initialize(stage_outputs, config, check=True):
    directory = "stages/03-kubernetes-initialize"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars={
            'name': config['project_name'],
            'environment': config['namespace'],
            'cloud-provider': config['provider'],
            'aws-region': config.get('amazon_web_services', {}).get('region'),
        },
        terraform_objects=[
            QHubTerraformState('03-kubernetes-initialize', config),
            QHubKubernetesProvider(config),
        ])

    if check:
        check_03_kubernetes_initialize(stage_outputs, config)


def check_03_kubernetes_initialize(stage_outputs, qhub_config):
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    directory = "stages/03-kubernetes-initialize"
    config.load_kube_config(
        config_file=stage_outputs['stages/02-infrastructure']['kubeconfig_filename']['value'])

    try:
        api_instance = client.CoreV1Api()
        result = api_instance.list_namespace()
    except ApiException:
        print(f'ERROR: After stage directory={directory} unable to connect to kubernetes cluster')
        sys.exit(1)

    namespaces = {_.metadata.name for _ in result.items}
    if qhub_config['namespace'] not in namespaces:
        print(f"ERROR: After stage directory={directory} namespace={config['namespace']} not provisioned within kubernetes cluster")
        sys.exit(1)

    print(f'After stage directory={directory} kubernetes initialized successfully')


def provision_04_kubernetes_ingress(stage_outputs, config, check=True):
    directory = "stages/04-kubernetes-ingress"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars={
            'name': config['project_name'],
            'environment': config['namespace'],
            "node_groups": calculate_note_groups(config),
            "enable-certificates": (config['certificate']['type'] == 'lets-encrypt'),
            "acme-email": config['certificate'].get('acme_email'),
            "acme-server": config['certificate'].get('acme_server'),
            "certificate-secret-name": config['certificate']['secret_name'] if config['certificate']['type'] == 'existing' else None,
        },
        terraform_objects=[
            QHubTerraformState('04-kubernetes-ingress', config),
            QHubKubernetesProvider(config),
        ])

    if check:
        check_04_kubernetes_ingress(stage_outputs, config)


def check_04_kubernetes_ingress(stage_outputs, qhub_config):
    directory = "stages/04-kubernetes-ingress"

    import socket

    tcp_ports = {80, 443}
    ip_or_name = stage_outputs[directory]['load_balancer_address']['value']
    host = ip_or_name['hostname'] or ip_or_name['ip']

    for port in tcp_ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        result = s.connect_ex((host, port))
        if result != 0:
            print(f'ERROR: After stage directory={directory} unable to connect to ingress host={host} port={port}')
            sys.exit(1)
        s.close()

    print(f'After stage directory={directory} kubernetes ingress available on tcp ports={tcp_ports}')


def provision_ingress_dns(stage_outputs, config, dns_provider : str, dns_auto_provision : bool, disable_prompt : bool = True, check : bool = True):
    directory = "stages/04-kubernetes-ingress"

    ip_or_name = stage_outputs[directory]['load_balancer_address']['value']
    ip_or_hostname = ip_or_name['hostname'] or ip_or_name['ip']

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

    if check:
        check_ingress_dns(stage_outputs, config)


def check_ingress_dns(stage_outputs, config):
    import socket
    import time

    directory = "stages/04-kubernetes-ingress"
    domain_name = config['domain']
    ip_or_name = stage_outputs[directory]['load_balancer_address']['value']
    ip = socket.gethostbyname(ip_or_name['hostname'] or ip_or_name['ip'])

    lookup_count = 12
    lookup_interval = 5

    for i in range(lookup_count):
        try:
            resolved_ip = socket.gethostbyname(domain_name)
            if resolved_ip == ip:
                print(f'DNS configured domain={domain_name} matches ingress ip={ip}')
                break
            else:
                print(f'Polling DNS domain={domain_name} does not match ip={ip} instead got {resolved_ip}')
        except socket.gaierror:
            print(f'Polling DNS domain={domain_name} does not exist')
        time.sleep(lookup_interval)
    else:
        print(f'ERROR: After stage directory={directory} DNS domain={domain_name} does not point to ip={ip}')
        sys.exit(1)


def provision_05_kubernetes_keycloak(stage_outputs, config, check=True):
    directory = "stages/05-kubernetes-keycloak"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
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

    if check:
        check_05_kubernetes_keycloak(stage_outputs, config)


def check_05_kubernetes_keycloak(stage_outputs, config):
    directory = "stages/05-kubernetes-keycloak"

    from keycloak import KeycloakAdmin
    from keycloak.exceptions import KeycloakError

    keycloak_url = f"{stage_outputs[directory]['keycloak_credentials']['value']['url']}/auth/"

    try:
        realm_admin = KeycloakAdmin(
            keycloak_url,
            username=stage_outputs[directory]['keycloak_credentials']['value']['username'],
            password=stage_outputs[directory]['keycloak_credentials']['value']['password'],
            realm_name=stage_outputs[directory]['keycloak_credentials']['value']['realm'],
            client_id=stage_outputs[directory]['keycloak_credentials']['value']['client_id'],
            verify=False,
        )
    except KeycloakError:
        print(f'ERROR: unable to connect to keycloak at url={keycloak_url} with root credentials')
        sys.exit(1)

    print('Keycloak service within kubernetes started successfully')


def provision_06_kubernetes_keycloak_configuration(stage_outputs, config, check=True):
    directory = "stages/06-kubernetes-keycloak-configuration"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars={
            'realm': f"qhub-{config['project_name']}",
            'authentication': config['security']['authentication']
        },
        terraform_objects=[
            QHubTerraformState('06-kubernetes-keycloak-configuration', config),
        ])

    if check:
        check_06_kubernetes_keycloak_configuration(stage_outputs, config)


def check_06_kubernetes_keycloak_configuration(stage_outputs, config):
    directory = "stages/05-kubernetes-keycloak"

    from keycloak import KeycloakAdmin
    from keycloak.exceptions import KeycloakError

    keycloak_url = f"{stage_outputs[directory]['keycloak_credentials']['value']['url']}/auth/"

    try:
        realm_admin = KeycloakAdmin(
            keycloak_url,
            username=stage_outputs[directory]['keycloak_credentials']['value']['username'],
            password=stage_outputs[directory]['keycloak_credentials']['value']['password'],
            realm_name=stage_outputs[directory]['keycloak_credentials']['value']['realm'],
            client_id=stage_outputs[directory]['keycloak_credentials']['value']['client_id'],
            verify=False,
        )
        existing_realms = {_['id'] for _ in realm_admin.get_realms()}
        realm_id = stage_outputs['stages/06-kubernetes-keycloak-configuration']['realm_id']['value']
        if realm_id in existing_realms:
            print('Keycloak service within kubernetes configured successfully')
        else:
            print(f'ERROR: realm_id={realm_id} not in existing_realms={existing_realms} keycloak configuration failed')
            sys.exit(1)
    except KeycloakError:
        print(f'ERROR: unable to connect to keycloak at url={keycloak_url} with root credentials')
        sys.exit(1)


def provision_07_kubernetes_services(stage_outputs, config, check=True):
    directory = "stages/07-kubernetes-services"

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
            "jupyterhub-shared-endpoint": stage_outputs['stages/02-infrastructure'].get('nfs_endpoint'),
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

    if check:
        check_07_kubernetes_services(stage_outputs, config)


def check_07_kubernetes_services(stage_outputs, config):
    directory = "stages/07-kubernetes-services"
    import requests

    # supress insecure warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    services = stage_outputs[directory]['service_urls']['value']
    for service_name, service in services.items():
        service_url = service['health_url']
        response = requests.get(service_url, verify=False)
        if response.status_code < 400:
            print(f'Service {service_name} UP as url={service_url}')
        else:
            print(f'ERROR: Service {service_name} DOWN when checking url={service_url}')
            sys.exit(1)


def provision_08_enterprise_qhub(stage_outputs, config, check=True):
    directory = "stages/08-enterprise-qhub"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars={
            'environment': config['namespace'],
            "endpoint": config['domain'],
            "realm_id": stage_outputs['stages/06-kubernetes-keycloak-configuration']['realm_id']['value'],
            'tf_extensions': config.get('tf_extensions', []),
            'external_container_reg': config.get('external_container_reg', {'enabled': False}),
            'qhub_config': config,
            'helm_extensions': config.get('helm_extensions', []),
        },
        terraform_objects=[
            QHubTerraformState('08-enterprise-qhub', config),
            QHubKubernetesProvider(config),
        ])

    if check:
        pass


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

    stage_outputs = {}
    provision_01_terraform_state(stage_outputs, config)
    provision_02_infrastructure(stage_outputs, config)

    with kubernetes_provider_context(
            stage_outputs['stages/02-infrastructure']['kubernetes_credentials']['value']):
        provision_03_kubernetes_initialize(stage_outputs, config)
        provision_04_kubernetes_ingress(stage_outputs, config)
        provision_ingress_dns(stage_outputs, config, dns_provider=dns_provider, dns_auto_provision=dns_auto_provision, disable_prompt=disable_prompt)
        provision_05_kubernetes_keycloak(stage_outputs, config)

        with keycloak_provider_context(
                stage_outputs['stages/05-kubernetes-keycloak']['keycloak_credentials']['value']):
            provision_06_kubernetes_keycloak_configuration(stage_outputs, config)
            provision_07_kubernetes_services(stage_outputs, config)
            provision_08_enterprise_qhub(stage_outputs, config)

            print('QHub deployed successfully')

    print('Services:')
    for service_name, service in stage_outputs['stages/07-kubernetes-services']['service_urls']['value'].items():
        print(f" - {service_name} -> {service['url']}")

    print(f"Kubenetes kubeconfig located at file://{stage_outputs['stages/02-infrastructure']['kubeconfig_filename']['value']}")
    print(f"Kubecloak master realm username={stage_outputs['stages/05-kubernetes-keycloak']['keycloak_credentials']['value']['username']} password=file://{os.path.join(tempfile.gettempdir(), 'QHUB_DEFAULT_PASSWORD')}")
    print("Additional administration docs can be found at https://docs.qhub.dev/en/stable/source/admin_guide/")


def add_clearml_dns(zone_name, record_name, record_type, ip_or_hostname):
    logger.info(f"Setting DNS record for ClearML for record: {record_name}")
    dns_records = [
        f"app.clearml.{record_name}",
        f"api.clearml.{record_name}",
        f"files.clearml.{record_name}",
    ]

    for dns_record in dns_records:
        update_record(zone_name, dns_record, record_type, ip_or_hostname)
