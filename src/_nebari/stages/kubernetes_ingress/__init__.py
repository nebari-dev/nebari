import socket
import enum
import sys
import time
import typing
from typing import Any, Dict, List

from _nebari import constants
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
            if config.clearml.enabled:
                add_clearml_dns(zone_name, record_name, "A", ip_or_hostname)

        elif config.provider == schema.ProviderEnum.aws:
            update_record(zone_name, record_name, "CNAME", ip_or_hostname)
            if config.clearml.enabled:
                add_clearml_dns(zone_name, record_name, "CNAME", ip_or_hostname)
        else:
            logger.info(
                f"Couldn't update the DNS record for cloud provider: {config.provider}"
            )
    elif not disable_prompt:
        input(
            f"Take IP Address {ip_or_hostname} and update DNS to point to "
            f'"{config.domain}" [Press Enter when Complete]'
        )

    if not disable_checks:
        checks.check_ingress_dns(stage_outputs, config, disable_prompt)


def check_ingress_dns(stage_outputs, config, disable_prompt):
    directory = "stages/04-kubernetes-ingress"

    ip_or_name = stage_outputs[directory]["load_balancer_address"]["value"]
    ip = socket.gethostbyname(ip_or_name["hostname"] or ip_or_name["ip"])
    domain_name = stage_outputs[directory]["domain"]

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
    secret_name: typing.Optional[str]
    # lets-encrypt
    acme_email: typing.Optional[str]
    acme_server: str = "https://acme-v02.api.letsencrypt.org/directory"


class Ingress(schema.Base):
    terraform_overrides: typing.Dict = {}


class InputSchema(schema.Base):
    domain: typing.Optional[str]
    certificate: Certificate = Certificate()
    ingress: Ingress = Ingress()


class IngressEndpoint(schema.Base):
    ip: str
    hostname: str


class OutputSchema(schema.Base):
    load_balancer_address: typing.List[IngressEndpoint]
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

        print(
            f"After stage={self.name} kubernetes ingress available on tcp ports={tcp_ports}"
        )

        check_ingress_dns(stage_outputs, self.config, disable_prompt=False)


@hookimpl
def nebari_stage() -> List[NebariStage]:
    return [KubernetesIngressStage]
