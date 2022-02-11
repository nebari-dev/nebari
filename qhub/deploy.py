import socket
import time
import logging
import os
import sys
import contextlib
from subprocess import CalledProcessError
from typing import Dict
import tempfile
import json

from qhub.provider import terraform
from qhub.utils import (
    timer,
    check_cloud_credentials,
    modified_environ,
    split_docker_image_name,
)
from qhub.provider.dns.cloudflare import update_record


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
def kubernetes_provider_context(kubernetes_credentials: Dict[str, str]):
    credential_mapping = {
        "config_path": "KUBE_CONFIG_PATH",
        "config_context": "KUBE_CTX",
        "username": "KUBE_USER",
        "password": "KUBE_PASSWORD",
        "client_certificate": "KUBE_CLIENT_CERT_DATA",
        "client_key": "KUBE_CLIENT_KEY_DATA",
        "cluster_ca_certificate": "KUBE_CLUSTER_CA_CERT_DATA",
        "host": "KUBE_HOST",
        "token": "KUBE_TOKEN",
    }

    credentials = {
        credential_mapping[k]: v
        for k, v in kubernetes_credentials.items()
        if v is not None
    }
    with modified_environ(**credentials):
        yield


@contextlib.contextmanager
def keycloak_provider_context(keycloak_credentials: Dict[str, str]):
    credential_mapping = {
        "client_id": "KEYCLOAK_CLIENT_ID",
        "url": "KEYCLOAK_URL",
        "username": "KEYCLOAK_USER",
        "password": "KEYCLOAK_PASSWORD",
        "realm": "KEYCLOAK_REALM",
    }

    credentials = {credential_mapping[k]: v for k, v in keycloak_credentials.items()}
    with modified_environ(**credentials):
        yield


def calculate_note_groups(config):
    if config["provider"] == "aws":
        return {
            group: {"key": "eks.amazonaws.com/nodegroup", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config["provider"] == "gcp":
        return {
            group: {"key": "cloud.google.com/gke-nodepool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config["provider"] == "azure":
        return {
            group: {"key": "azure-node-pool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config["provider"] == "do":
        return {
            group: {"key": "doks.digitalocean.com/node-pool", "value": group}
            for group in ["general", "user", "worker"]
        }
    else:
        return config["local"]["node_selectors"]


def provision_01_terraform_state(stage_outputs, config):
    directory = "stages/01-terraform-state"

    if config["provider"] == "local":
        stage_outputs[directory] = {}
    elif config["provider"] == "do":
        stage_outputs[directory] = terraform.deploy(
            terraform_import=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "namespace": config["namespace"],
                "region": config["digital_ocean"]["region"],
            },
            state_imports=[
                (
                    "module.terraform-state.module.spaces.digitalocean_spaces_bucket.main",
                    f"{config['digital_ocean']['region']},{config['project_name']}-{config['namespace']}-terraform-state",
                )
            ],
        )
    elif config["provider"] == "gcp":
        stage_outputs[directory] = terraform.deploy(
            terraform_import=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "namespace": config["namespace"],
                "region": config["google_cloud_platform"]["region"],
            },
            state_imports=[
                (
                    "module.terraform-state.module.gcs.google_storage_bucket.static-site",
                    f"{config['project_name']}-{config['namespace']}-terraform-state",
                )
            ],
        )
    elif config["provider"] == "azure":
        subscription_id = os.environ["ARM_SUBSCRIPTION_ID"]
        resource_group_name = f"{config['project_name']}-{config['namespace']}"
        resource_group_name_safe = resource_group_name.replace("-", "")
        resource_group_url = f"/subscriptions/{subscription_id}/resourceGroups/{config['project_name']}-{config['namespace']}"

        stage_outputs[directory] = terraform.deploy(
            terraform_import=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "namespace": config["namespace"],
                "region": config["azure"]["region"],
                "storage_account_postfix": config["azure"]["storage_account_postfix"],
            },
            state_imports=[
                (
                    "module.terraform-state.azurerm_resource_group.terraform-resource-group",
                    resource_group_url,
                ),
                (
                    "module.terraform-state.azurerm_storage_account.terraform-storage-account",
                    f"{resource_group_url}/providers/Microsoft.Storage/storageAccounts/{resource_group_name_safe}{config['azure']['storage_account_postfix']}",
                ),
                (
                    "module.terraform-state.azurerm_storage_container.storage_container",
                    f"https://{resource_group_name_safe}{config['azure']['storage_account_postfix']}.blob.core.windows.net/{resource_group_name}state",
                ),
            ],
        )
    elif config["provider"] == "aws":
        stage_outputs[directory] = terraform.deploy(
            terraform_import=True,
            directory=os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "namespace": config["namespace"],
            },
            state_imports=[
                (
                    "module.terraform-state.aws_s3_bucket.terraform-state",
                    f"{config['project_name']}-{config['namespace']}-terraform-state",
                ),
                (
                    "module.terraform-state.aws_dynamodb_table.terraform-state-lock",
                    f"{config['project_name']}-{config['namespace']}-terraform-state-lock",
                ),
            ],
        )
    else:
        raise NotImplementedError(
            f'provider {config["provider"]} not implemented for directory={directory}'
        )


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
    directory = "stages/02-infrastructure"

    if config["provider"] == "local":
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config["provider"]),
            input_vars={"kube_context": config["local"].get("kube_context")},
        )
    elif config["provider"] == "do":
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "environment": config["namespace"],
                "region": config["digital_ocean"]["region"],
                "kubernetes_version": config["digital_ocean"]["kubernetes_version"],
                "node_groups": config["digital_ocean"]["node_groups"],
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "QHUB_KUBECONFIG"
                ),
            },
        )
    elif config["provider"] == "gcp":
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "environment": config["namespace"],
                "region": config["google_cloud_platform"]["region"],
                "project_id": config["google_cloud_platform"]["project"],
                "node_groups": [
                    {
                        "name": key,
                        "min_size": value["min_nodes"],
                        "max_size": value["max_nodes"],
                        "instance_type": value["instance"],
                        **value,
                    }
                    for key, value in config["google_cloud_platform"][
                        "node_groups"
                    ].items()
                ],
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "QHUB_KUBECONFIG"
                ),
            },
        )
    elif config["provider"] == "azure":
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "environment": config["namespace"],
                "region": config["azure"]["region"],
                "kubernetes_version": config["azure"]["kubernetes_version"],
                "node_groups": config["azure"]["node_groups"],
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "QHUB_KUBECONFIG"
                ),
            },
        )
    elif config["provider"] == "aws":
        stage_outputs[directory] = terraform.deploy(
            os.path.join(directory, config["provider"]),
            input_vars={
                "name": config["project_name"],
                "environment": config["namespace"],
                "node_groups": [
                    {
                        "name": key,
                        "min_size": value["min_nodes"],
                        "desired_size": value["min_nodes"],
                        "max_size": value["max_nodes"],
                        "gpu": value.get("gpu", False),
                        "instance_type": value["instance"],
                    }
                    for key, value in config["amazon_web_services"][
                        "node_groups"
                    ].items()
                ],
                "kubeconfig_filename": os.path.join(
                    tempfile.gettempdir(), "QHUB_KUBECONFIG"
                ),
            },
        )
    else:
        raise NotImplementedError(
            f'provider {config["provider"]} not implemented for directory={directory}'
        )

    if check:
        check_02_infrastructure(stage_outputs, config)


def check_02_infrastructure(stage_outputs, qhub_config):
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    directory = "stages/02-infrastructure"
    config.load_kube_config(
        config_file=stage_outputs["stages/02-infrastructure"]["kubeconfig_filename"][
            "value"
        ]
    )

    try:
        api_instance = client.CoreV1Api()
        result = api_instance.list_node()
    except ApiException:
        print(
            f"ERROR: After stage directory={directory} unable to connect to kubernetes cluster"
        )
        sys.exit(1)

    if len(result.items) < 1:
        print(
            f"ERROR: After stage directory={directory} no nodes provisioned within kubernetes cluster"
        )
        sys.exit(1)

    print(
        f"After stage directory={directory} kubernetes cluster successfully provisioned"
    )


def provision_03_kubernetes_initialize(stage_outputs, config, check=True):
    directory = "stages/03-kubernetes-initialize"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars={
            "name": config["project_name"],
            "environment": config["namespace"],
            "cloud-provider": config["provider"],
            "aws-region": config.get("amazon_web_services", {}).get("region"),
            "external_container_reg": config.get(
                "external_container_reg", {"enabled": False}
            ),
        },
    )

    if check:
        check_03_kubernetes_initialize(stage_outputs, config)


def check_03_kubernetes_initialize(stage_outputs, qhub_config):
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    directory = "stages/03-kubernetes-initialize"
    config.load_kube_config(
        config_file=stage_outputs["stages/02-infrastructure"]["kubeconfig_filename"][
            "value"
        ]
    )

    try:
        api_instance = client.CoreV1Api()
        result = api_instance.list_namespace()
    except ApiException:
        print(
            f"ERROR: After stage directory={directory} unable to connect to kubernetes cluster"
        )
        sys.exit(1)

    namespaces = {_.metadata.name for _ in result.items}
    if qhub_config["namespace"] not in namespaces:
        print(
            f"ERROR: After stage directory={directory} namespace={config['namespace']} not provisioned within kubernetes cluster"
        )
        sys.exit(1)

    print(f"After stage directory={directory} kubernetes initialized successfully")


def provision_04_kubernetes_ingress(stage_outputs, config, check=True):
    directory = "stages/04-kubernetes-ingress"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars={
            "name": config["project_name"],
            "environment": config["namespace"],
            "node_groups": calculate_note_groups(config),
            "enable-certificates": (config["certificate"]["type"] == "lets-encrypt"),
            "acme-email": config["certificate"].get("acme_email"),
            "acme-server": config["certificate"].get("acme_server"),
            "certificate-secret-name": config["certificate"]["secret_name"]
            if config["certificate"]["type"] == "existing"
            else None,
        },
    )

    if check:
        check_04_kubernetes_ingress(stage_outputs, config)


def check_04_kubernetes_ingress(stage_outputs, qhub_config):
    directory = "stages/04-kubernetes-ingress"

    def _attempt_tcp_connect(host, port, num_attempts=3, timeout=5):
        # normalize hostname to ip address
        host = socket.gethostbyname(host)

        for i in range(num_attempts):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            result = s.connect_ex((host, port))
            if result == 0:
                print(f"Attempt {i+1} succedded to connect to tcp://{host}:{port}")
                return True
            s.close()
            print(f"Attempt {i+1} failed to connect to tcp tcp://{host}:{port}")
            time.sleep(timeout)
        return False

    tcp_ports = {
        80,  # http
        443,  # https
        8022,  # jupyterhub-ssh ssh
        8023,  # jupyterhub-ssh sftp
        9080,  # minio
        8786,  # dask-scheduler
    }
    ip_or_name = stage_outputs[directory]["load_balancer_address"]["value"]
    host = ip_or_name["hostname"] or ip_or_name["ip"]

    for port in tcp_ports:
        if not _attempt_tcp_connect(host, port):
            print(
                f"ERROR: After stage directory={directory} unable to connect to ingress host={host} port={port}"
            )
            sys.exit(1)

    print(
        f"After stage directory={directory} kubernetes ingress available on tcp ports={tcp_ports}"
    )


def provision_ingress_dns(
    stage_outputs,
    config,
    dns_provider: str,
    dns_auto_provision: bool,
    disable_prompt: bool = True,
    check: bool = True,
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

    if check:
        check_ingress_dns(stage_outputs, config)


def check_ingress_dns(stage_outputs, config):
    directory = "stages/04-kubernetes-ingress"

    ip_or_name = stage_outputs[directory]["load_balancer_address"]["value"]
    ip = socket.gethostbyname(ip_or_name["hostname"] or ip_or_name["ip"])
    domain_name = config["domain"]

    def _attempt_dns_lookup(domain_name, ip, num_attempts=12, timeout=5):
        for i in range(num_attempts):
            try:
                resolved_ip = socket.gethostbyname(domain_name)
                if resolved_ip == ip:
                    print(
                        f"DNS configured domain={domain_name} matches ingress ip={ip}"
                    )
                    return True
                else:
                    print(
                        f"Attempt {i+1} polling DNS domain={domain_name} does not match ip={ip} instead got {resolved_ip}"
                    )
            except socket.gaierror:
                print(
                    f"Attempt {i+1} polling DNS domain={domain_name} record does not exist"
                )
            time.sleep(timeout)
        return False

    if not _attempt_dns_lookup(domain_name, ip):
        print(
            f"ERROR: After stage directory={directory} DNS domain={domain_name} does not point to ip={ip}"
        )
        sys.exit(1)


def provision_05_kubernetes_keycloak(stage_outputs, config, check=True):
    directory = "stages/05-kubernetes-keycloak"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars={
            "name": config["project_name"],
            "environment": config["namespace"],
            "endpoint": config["domain"],
            "initial-root-password": config["security"]["keycloak"][
                "initial_root_password"
            ],
            "overrides": [
                json.dumps(config["security"]["keycloak"].get("overrides", {}))
            ],
            "node-group": calculate_note_groups(config)["general"],
        },
    )

    if check:
        check_05_kubernetes_keycloak(stage_outputs, config)


def check_05_kubernetes_keycloak(stage_outputs, config):
    directory = "stages/05-kubernetes-keycloak"

    from keycloak import KeycloakAdmin
    from keycloak.exceptions import KeycloakError

    keycloak_url = (
        f"{stage_outputs[directory]['keycloak_credentials']['value']['url']}/auth/"
    )

    def _attempt_keycloak_connection(
        keycloak_url,
        username,
        password,
        realm_name,
        client_id,
        verify=False,
        num_attempts=3,
        timeout=5,
    ):
        for i in range(num_attempts):
            try:
                KeycloakAdmin(
                    keycloak_url,
                    username=username,
                    password=password,
                    realm_name=realm_name,
                    client_id=client_id,
                    verify=verify,
                )
                print(f"Attempt {i+1} succeded connecting to keycloak master realm")
                return True
            except KeycloakError:
                print(f"Attempt {i+1} failed connecting to keycloak master realm")
            time.sleep(timeout)
        return False

    if not _attempt_keycloak_connection(
        keycloak_url,
        stage_outputs[directory]["keycloak_credentials"]["value"]["username"],
        stage_outputs[directory]["keycloak_credentials"]["value"]["password"],
        stage_outputs[directory]["keycloak_credentials"]["value"]["realm"],
        stage_outputs[directory]["keycloak_credentials"]["value"]["client_id"],
        verify=False,
    ):
        print(
            f"ERROR: unable to connect to keycloak master realm at url={keycloak_url} with root credentials"
        )
        sys.exit(1)

    print("Keycloak service successfully started")


def provision_06_kubernetes_keycloak_configuration(stage_outputs, config, check=True):
    directory = "stages/06-kubernetes-keycloak-configuration"
    realm_id = f"qhub-{config['project_name']}"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars={
            "realm": realm_id,
            "realm_display_name": config["security"]["keycloak"].get(
                "realm_display_name", realm_id
            ),
            "authentication": config["security"]["authentication"],
        },
    )

    if check:
        check_06_kubernetes_keycloak_configuration(stage_outputs, config)


def check_06_kubernetes_keycloak_configuration(stage_outputs, config):
    directory = "stages/05-kubernetes-keycloak"

    from keycloak import KeycloakAdmin
    from keycloak.exceptions import KeycloakError

    keycloak_url = (
        f"{stage_outputs[directory]['keycloak_credentials']['value']['url']}/auth/"
    )

    def _attempt_keycloak_connection(
        keycloak_url,
        username,
        password,
        realm_name,
        client_id,
        qhub_realm,
        verify=False,
        num_attempts=5,
        timeout=10,
    ):
        for i in range(num_attempts):
            try:
                realm_admin = KeycloakAdmin(
                    keycloak_url,
                    username=username,
                    password=password,
                    realm_name=realm_name,
                    client_id=client_id,
                    verify=verify,
                )
                existing_realms = {_["id"] for _ in realm_admin.get_realms()}
                if qhub_realm in existing_realms:
                    print(
                        f"Attempt {i+1} succeded connecting to keycloak and qhub realm={qhub_realm} exists"
                    )
                    return True
                else:
                    print(
                        f"Attempt {i+1} succeeded connecting to keycloak but qhub realm did not exist"
                    )
            except KeycloakError:
                print(f"Attempt {i+1} failed connecting to keycloak master realm")
            time.sleep(timeout)
        return False

    if not _attempt_keycloak_connection(
        keycloak_url,
        stage_outputs[directory]["keycloak_credentials"]["value"]["username"],
        stage_outputs[directory]["keycloak_credentials"]["value"]["password"],
        stage_outputs[directory]["keycloak_credentials"]["value"]["realm"],
        stage_outputs[directory]["keycloak_credentials"]["value"]["client_id"],
        qhub_realm=stage_outputs["stages/06-kubernetes-keycloak-configuration"][
            "realm_id"
        ]["value"],
        verify=False,
    ):
        print(
            "ERROR: unable to connect to keycloak master realm and ensure that qhub realm exists"
        )
        sys.exit(1)

    print("Keycloak service successfully started with qhub realm")


def provision_07_kubernetes_services(stage_outputs, config, check=True):
    directory = "stages/07-kubernetes-services"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars={
            "name": config["project_name"],
            "environment": config["namespace"],
            "endpoint": config["domain"],
            "realm_id": stage_outputs["stages/06-kubernetes-keycloak-configuration"][
                "realm_id"
            ]["value"],
            "node_groups": calculate_note_groups(config),
            # conda-store
            "conda-store-environments": config["environments"],
            "conda-store-storage": config["storage"]["conda_store"],
            "conda-store-image": split_docker_image_name(
                config["default_images"]["conda_store"]
            ),
            # jupyterhub
            "cdsdashboards": config["cdsdashboards"],
            "jupyterhub-theme": config["theme"]["jupyterhub"],
            "jupyterhub-image": split_docker_image_name(
                config["default_images"]["jupyterhub"]
            ),
            "jupyterhub-shared-storage": config["storage"]["shared_filesystem"],
            "jupyterhub-shared-endpoint": stage_outputs["stages/02-infrastructure"]
            .get("nfs_endpoint", {})
            .get("value"),
            "jupyterlab-profiles": config["profiles"]["jupyterlab"],
            "jupyterlab-image": split_docker_image_name(
                config["default_images"]["jupyterlab"]
            ),
            "jupyterhub-overrides": [
                json.dumps(config.get("jupyterhub", {}).get("overrides", {}))
            ],
            # dask-gateway
            "dask-gateway-image": split_docker_image_name(
                config["default_images"]["dask_gateway"]
            ),
            "dask-worker-image": split_docker_image_name(
                config["default_images"]["dask_worker"]
            ),
            "dask-gateway-profiles": config["profiles"]["dask_worker"],
            # monitoring
            "monitoring-enabled": config["monitoring"]["enabled"],
            # prefect
            "prefect-enabled": config.get("prefect", {}).get("enabled", False),
            "prefect-token": config.get("prefect", {}).get("token", ""),
            "prefect-image": config.get("prefect", {}).get("image", ""),
            "prefect-overrides": config.get("prefect", {}).get("overrides", {}),
            # clearml
            "clearml-enabled": config.get("clearml", {}).get("enabled", False),
            "clearml-enable-forwardauth": config.get("clearml", {}).get(
                "enable_forward_auth", False
            ),
        },
    )

    if check:
        check_07_kubernetes_services(stage_outputs, config)


def check_07_kubernetes_services(stage_outputs, config):
    directory = "stages/07-kubernetes-services"
    import requests

    # supress insecure warnings
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _attempt_connect_url(url, verify=False, num_attempts=3, timeout=5):
        for i in range(num_attempts):
            response = requests.get(service_url, verify=verify)
            if response.status_code < 400:
                print(f"Attempt {i+1} health check succeded for url={url}")
                return True
            else:
                print(f"Attempt {i+1} health check failed for url={url}")
        return False

    services = stage_outputs[directory]["service_urls"]["value"]
    for service_name, service in services.items():
        service_url = service["health_url"]
        if not _attempt_connect_url(service_url):
            print(f"ERROR: Service {service_name} DOWN when checking url={service_url}")
            sys.exit(1)


def provision_08_enterprise_qhub(stage_outputs, config, check=True):
    directory = "stages/08-enterprise-qhub"

    stage_outputs[directory] = terraform.deploy(
        directory=directory,
        input_vars={
            "environment": config["namespace"],
            "endpoint": config["domain"],
            "realm_id": stage_outputs["stages/06-kubernetes-keycloak-configuration"][
                "realm_id"
            ]["value"],
            "tf_extensions": config.get("tf_extensions", []),
            "qhub_config": config,
            "helm_extensions": config.get("helm_extensions", []),
        },
    )

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
    if config["provider"] != "local" and config["terraform_state"]["type"] == "remote":
        provision_01_terraform_state(stage_outputs, config)
    provision_02_infrastructure(stage_outputs, config)

    with kubernetes_provider_context(
        stage_outputs["stages/02-infrastructure"]["kubernetes_credentials"]["value"]
    ):
        provision_03_kubernetes_initialize(stage_outputs, config)
        provision_04_kubernetes_ingress(stage_outputs, config)
        provision_ingress_dns(
            stage_outputs,
            config,
            dns_provider=dns_provider,
            dns_auto_provision=dns_auto_provision,
            disable_prompt=disable_prompt,
        )
        provision_05_kubernetes_keycloak(stage_outputs, config)

        with keycloak_provider_context(
            stage_outputs["stages/05-kubernetes-keycloak"]["keycloak_credentials"][
                "value"
            ]
        ):
            provision_06_kubernetes_keycloak_configuration(stage_outputs, config)
            provision_07_kubernetes_services(stage_outputs, config)
            provision_08_enterprise_qhub(stage_outputs, config)

            print("QHub deployed successfully")

    print("Services:")
    for service_name, service in stage_outputs["stages/07-kubernetes-services"][
        "service_urls"
    ]["value"].items():
        print(f" - {service_name} -> {service['url']}")

    print(
        f"Kubenetes kubeconfig located at file://{stage_outputs['stages/02-infrastructure']['kubeconfig_filename']['value']}"
    )
    print(
        f"Kubecloak master realm username={stage_outputs['stages/05-kubernetes-keycloak']['keycloak_credentials']['value']['username']} password=file://{os.path.join(tempfile.gettempdir(), 'QHUB_DEFAULT_PASSWORD')}"
    )
    print(
        "Additional administration docs can be found at https://docs.qhub.dev/en/stable/source/admin_guide/"
    )


def add_clearml_dns(zone_name, record_name, record_type, ip_or_hostname):
    logger.info(f"Setting DNS record for ClearML for record: {record_name}")
    dns_records = [
        f"app.clearml.{record_name}",
        f"api.clearml.{record_name}",
        f"files.clearml.{record_name}",
    ]

    for dns_record in dns_records:
        update_record(zone_name, dns_record, record_type, ip_or_hostname)
