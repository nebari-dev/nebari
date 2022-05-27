import socket
import sys
import time

# check and retry settings
NUM_ATTEMPTS = 10
TIMEOUT = 10  # seconds


def stage_02_infrastructure(stage_outputs, qhub_config):
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
        result = api_instance.list_namespace()
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


def stage_03_kubernetes_initialize(stage_outputs, qhub_config):
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


def stage_04_kubernetes_ingress(stage_outputs, qhub_config):
    directory = "stages/04-kubernetes-ingress"

    def _attempt_tcp_connect(host, port, num_attempts=NUM_ATTEMPTS, timeout=TIMEOUT):
        for i in range(num_attempts):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # normalize hostname to ip address
                ip = socket.gethostbyname(host)
                s.settimeout(5)
                result = s.connect_ex((ip, port))
                if result == 0:
                    print(f"Attempt {i+1} succeeded to connect to tcp://{ip}:{port}")
                    return True
                print(f"Attempt {i+1} failed to connect to tcp tcp://{ip}:{port}")
            except socket.gaierror:
                print(f"Attempt {i+1} failed to get IP for {host}...")
            finally:
                s.close()

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
    host = host.strip("\n")

    for port in tcp_ports:
        if not _attempt_tcp_connect(host, port):
            print(
                f"ERROR: After stage directory={directory} unable to connect to ingress host={host} port={port}"
            )
            sys.exit(1)

    print(
        f"After stage directory={directory} kubernetes ingress available on tcp ports={tcp_ports}"
    )


def check_ingress_dns(stage_outputs, config, disable_prompt):
    directory = "stages/04-kubernetes-ingress"

    ip_or_name = stage_outputs[directory]["load_balancer_address"]["value"]
    ip = socket.gethostbyname(ip_or_name["hostname"] or ip_or_name["ip"])
    domain_name = config["domain"]

    def _attempt_dns_lookup(
        domain_name, ip, num_attempts=NUM_ATTEMPTS, timeout=TIMEOUT
    ):
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

    attempt = 0
    while not _attempt_dns_lookup(domain_name, ip):
        sleeptime = 60 * (2**attempt)
        if not disable_prompt:
            input(
                f"After attempting to poll the DNS, the record for domain={domain_name} appears not to exist, "
                f"has recently been updated, or has yet to fully propagate. This non-deterministic behavior is likely due to "
                f"DNS caching and will likely resolve itself in a few minutes.\n\n\tTo poll the DNS again in {sleeptime} seconds "
                f"[Press Enter].\n\n...otherwise kill the process and run the deployment again later..."
            )

        print(f"Will attempt to poll DNS again in {sleeptime} seconds...")
        time.sleep(sleeptime)
        attempt += 1
        if attempt == 5:
            print(
                f"ERROR: After stage directory={directory} DNS domain={domain_name} does not point to ip={ip}"
            )
            sys.exit(1)


def stage_05_kubernetes_keycloak(stage_outputs, config):
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
        num_attempts=NUM_ATTEMPTS,
        timeout=TIMEOUT,
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
                print(f"Attempt {i+1} succeeded connecting to keycloak master realm")
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


def stage_06_kubernetes_keycloak_configuration(stage_outputs, config):
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
        num_attempts=NUM_ATTEMPTS,
        timeout=TIMEOUT,
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
                        f"Attempt {i+1} succeeded connecting to keycloak and qhub realm={qhub_realm} exists"
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


def stage_07_kubernetes_services(stage_outputs, config):
    directory = "stages/07-kubernetes-services"
    import requests

    # suppress insecure warnings
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _attempt_connect_url(
        url, verify=False, num_attempts=NUM_ATTEMPTS, timeout=TIMEOUT
    ):
        for i in range(num_attempts):
            response = requests.get(url, verify=verify, timeout=timeout)
            if response.status_code < 400:
                print(f"Attempt {i+1} health check succeeded for url={url}")
                return True
            else:
                print(f"Attempt {i+1} health check failed for url={url}")
            time.sleep(timeout)
        return False

    services = stage_outputs[directory]["service_urls"]["value"]
    for service_name, service in services.items():
        service_url = service["health_url"]
        if service_url and not _attempt_connect_url(service_url):
            print(f"ERROR: Service {service_name} DOWN when checking url={service_url}")
            sys.exit(1)
