import pathlib
import socket
import sys
from typing import Any, Dict, List

from _nebari import constants, schema
from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl

# check and retry settings
NUM_ATTEMPTS = 10
TIMEOUT = 10  # seconds


def _calculate_node_groups(config: schema.Main):
    if config.provider == schema.ProviderEnum.aws:
        return {
            group: {"key": "eks.amazonaws.com/nodegroup", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.gcp:
        return {
            group: {"key": "cloud.google.com/gke-nodepool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.azure:
        return {
            group: {"key": "azure-node-pool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.do:
        return {
            group: {"key": "doks.digitalocean.com/node-pool", "value": group}
            for group in ["general", "user", "worker"]
        }
    elif config.provider == schema.ProviderEnum.existing:
        return config.existing.node_selectors
    else:
        return config.local.node_selectors


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


class KubernetesIngressStage(NebariTerraformStage):
    name = "04-kubernetes-ingress"
    priority = 40

    def tf_objects(self) -> List[Dict]:
        return [
            NebariTerraformState(self.name, self.config),
            NebariKubernetesProvider(self.config),
            NebariHelmProvider(self.config),
        ]

    def input_vars(self, stage_outputs: Dict[str, Dict[str, Any]]):
        cert_type = self.config.certificate.type
        cert_details = {"certificate-service": cert_type}
        if cert_type == "lets-encrypt":
            cert_details["acme-email"] = self.config.certificate.acme_email
            cert_details["acme-server"] = self.config.certificate.acme_server
        elif cert_type == "existing":
            cert_details[
                "certificate-secret-name"
            ] = self.config.certificate.secret_name

        return {
            **{
                "traefik-image": {
                    "image": "traefik",
                    "tag": constants.DEFAULT_TRAEFIK_IMAGE_TAG,
                },
                "name": self.config.project_name,
                "environment": self.config.namespace,
                "node_groups": _calculate_node_groups(self.config),
                **config.ingress.terraform_overrides,
            },
            **cert_details,
        }

    def check(self, stage_outputs: Dict[str, Dict[str, Any]]):
        def _attempt_tcp_connect(
            host, port, num_attempts=NUM_ATTEMPTS, timeout=TIMEOUT
        ):
            for i in range(num_attempts):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    # normalize hostname to ip address
                    ip = socket.gethostbyname(host)
                    s.settimeout(5)
                    result = s.connect_ex((ip, port))
                    if result == 0:
                        print(
                            f"Attempt {i+1} succeeded to connect to tcp://{ip}:{port}"
                        )
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
        ip_or_name = stage_outputs["stages/" + self.name]["load_balancer_address"][
            "value"
        ]
        host = ip_or_name["hostname"] or ip_or_name["ip"]
        host = host.strip("\n")

        for port in tcp_ports:
            if not _attempt_tcp_connect(host, port):
                print(
                    f"ERROR: After stage={self.name} unable to connect to ingress host={host} port={port}"
                )
                sys.exit(1)

        self.log.info(
            f"After stage={self.name} kubernetes ingress available on tcp ports={tcp_ports}"
        )

        check_ingress_dns(stage_outputs, self.config, disable_prompt=False)


@hookimpl
def nebari_stage(install_directory: pathlib.Path, config: schema.Main) -> [NebariStage]:
    return [
        KubernetesIngressStage(
            install_directory,
            config,
            template_directory=(pathlib.Path(__file__).parent / "template"),
            stage_prefix=pathlib.Path("stages/04-kubernetes-ingress"),
        )
    ]
