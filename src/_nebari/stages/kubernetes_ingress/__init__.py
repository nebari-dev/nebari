import enum
import logging
import socket
import sys
import time
from typing import Any, Dict, List, Optional, Type

from _nebari import constants
from _nebari.provider.dns.cloudflare import update_record
from _nebari.stages.base import NebariTerraformStage
from _nebari.stages.tf_objects import (
    NebariHelmProvider,
    NebariKubernetesProvider,
    NebariTerraformState,
)
from nebari import schema
from nebari.hookspecs import NebariStage, hookimpl

logger = logging.getLogger(__name__)

# check and retry settings
NUM_ATTEMPTS = 10
TIMEOUT = 10  # seconds


def provision_ingress_dns(
    stage_outputs: Dict[str, Dict[str, Any]],
    config: schema.Main,
    dns_provider: str,
    dns_auto_provision: bool,
    disable_prompt: bool = True,
):
    directory = "stages/04-kubernetes-ingress"

    ip_or_name = stage_outputs[directory]["load_balancer_address"]["value"]
    ip_or_hostname = ip_or_name["hostname"] or ip_or_name["ip"]

    if dns_auto_provision and dns_provider == "cloudflare":
        record_name, zone_name = (
            config.domain.split(".")[:-2],
            config.domain.split(".")[-2:],
        )
        record_name = ".".join(record_name)
        zone_name = ".".join(zone_name)
        if config.provider in {
            schema.ProviderEnum.do,
            schema.ProviderEnum.gcp,
            schema.ProviderEnum.azure,
        }:
            update_record(zone_name, record_name, "A", ip_or_hostname)

        elif config.provider == schema.ProviderEnum.aws:
            update_record(zone_name, record_name, "CNAME", ip_or_hostname)
        else:
            logger.info(
                f"Couldn't update the DNS record for cloud provider: {config.provider}"
            )
    elif not disable_prompt:
        input(
            f"Take IP Address {ip_or_hostname} and update DNS to point to "
            f'"{config.domain}" [Press Enter when Complete]'
        )


def check_ingress_dns(stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool):
    directory = "stages/04-kubernetes-ingress"

    ip_or_name = stage_outputs[directory]["load_balancer_address"]["value"]
    ip = socket.gethostbyname(ip_or_name["hostname"] or ip_or_name["ip"])
    domain_name = stage_outputs[directory]["domain"]

    def _attempt_dns_lookup(
        domain_name, ip, num_attempts=NUM_ATTEMPTS, timeout=TIMEOUT
    ):
        for i in range(num_attempts):
            try:
                _, _, resolved_ips = socket.gethostbyname_ex(domain_name)
                if ip in resolved_ips:
                    print(
                        f"DNS configured domain={domain_name} matches ingress ips={ip}"
                    )
                    return True
                else:
                    print(
                        f"Attempt {i+1} polling DNS domain={domain_name} does not match ip={ip} instead got {resolved_ips}"
                    )
            except socket.gaierror:
                print(
                    f"Attempt {i+1} polling DNS domain={domain_name} record does not exist"
                )
            time.sleep(timeout)
        return False

    attempt = 0
    while not _attempt_dns_lookup(domain_name, ip):
        if disable_prompt:
            sleeptime = 60 * (2**attempt)
            print(f"Will attempt to poll DNS again in {sleeptime} seconds...")
            time.sleep(sleeptime)
        else:
            input(
                f"After attempting to poll the DNS, the record for domain={domain_name} appears not to exist, "
                f"has recently been updated, or has yet to fully propagate. This non-deterministic behavior is likely due to "
                f"DNS caching and will likely resolve itself in a few minutes.\n\n\tTo poll the DNS again [Press Enter].\n\n"
                f"...otherwise kill the process and run the deployment again later..."
            )

        attempt += 1
        if attempt == 5:
            print(
                f"ERROR: After stage directory={directory} DNS domain={domain_name} does not point to ip={ip}"
            )
            sys.exit(1)


@schema.yaml_object(schema.yaml)
class CertificateEnum(str, enum.Enum):
    letsencrypt = "lets-encrypt"
    selfsigned = "self-signed"
    existing = "existing"
    disabled = "disabled"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_str(node.value)


class Certificate(schema.Base):
    type: CertificateEnum = CertificateEnum.selfsigned
    # existing
    secret_name: Optional[str] = None
    # lets-encrypt
    acme_email: Optional[str] = None
    acme_server: str = "https://acme-v02.api.letsencrypt.org/directory"


class DnsProvider(schema.Base):
    provider: Optional[str] = None
    auto_provision: Optional[bool] = False


class Ingress(schema.Base):
    terraform_overrides: Dict = {}


class InputSchema(schema.Base):
    domain: Optional[str] = None
    certificate: Certificate = Certificate()
    ingress: Ingress = Ingress()
    dns: DnsProvider = DnsProvider()


class IngressEndpoint(schema.Base):
    ip: str
    hostname: str


class OutputSchema(schema.Base):
    load_balancer_address: List[IngressEndpoint]
    domain: str


class KubernetesIngressStage(NebariTerraformStage):
    name = "04-kubernetes-ingress"
    priority = 40

    input_schema = InputSchema
    output_schema = OutputSchema

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
            cert_details["certificate-secret-name"] = (
                self.config.certificate.secret_name
            )

        return {
            **{
                "traefik-image": {
                    "image": "traefik",
                    "tag": constants.DEFAULT_TRAEFIK_IMAGE_TAG,
                },
                "name": self.config.project_name,
                "environment": self.config.namespace,
                "node_groups": stage_outputs["stages/02-infrastructure"][
                    "node_selectors"
                ],
                **self.config.ingress.terraform_overrides,
            },
            **cert_details,
        }

    def set_outputs(
        self, stage_outputs: Dict[str, Dict[str, Any]], outputs: Dict[str, Any]
    ):
        ip_or_name = outputs["load_balancer_address"]["value"]
        host = ip_or_name["hostname"] or ip_or_name["ip"]
        host = host.strip("\n")

        if self.config.domain is None:
            outputs["domain"] = host
        else:
            outputs["domain"] = self.config.domain

        super().set_outputs(stage_outputs, outputs)

    def post_deploy(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
        if self.config.dns and self.config.dns.provider:
            provision_ingress_dns(
                stage_outputs,
                self.config,
                dns_provider=self.config.dns.provider,
                dns_auto_provision=self.config.dns.auto_provision,
                disable_prompt=disable_prompt,
            )

    def check(
        self, stage_outputs: Dict[str, Dict[str, Any]], disable_prompt: bool = False
    ):
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

        print(
            f"After stage={self.name} kubernetes ingress available on tcp ports={tcp_ports}"
        )

        check_ingress_dns(stage_outputs, disable_prompt=disable_prompt)


@hookimpl
def nebari_stage() -> List[Type[NebariStage]]:
    return [KubernetesIngressStage]
