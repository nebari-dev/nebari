import logging
import os
import pathlib
import subprocess
import textwrap
import contextlib

from _nebari.provider import terraform
from _nebari.provider.dns.cloudflare import update_record
from _nebari.utils import (
    check_cloud_credentials,
    timer,
)
from _nebari.stages.base import get_available_stages
from nebari import schema


logger = logging.getLogger(__name__)


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
    config = schema.Main(**config)
    with contextlib.ExitStack() as stack:
        for stage in get_available_stages():
            s = stage(output_directory=pathlib.Path('.'), config=config)
            stack.enter_context(s.deploy(stage_outputs))
    print("Nebari deployed successfully")

    print("Services:")
    for service_name, service in stage_outputs["stages/07-kubernetes-services"][
        "service_urls"
    ]["value"].items():
        print(f" - {service_name} -> {service['url']}")

    print(
        f"Kubernetes kubeconfig located at file://{stage_outputs['stages/02-infrastructure']['kubeconfig_filename']['value']}"
    )
    username = "root"
    password = config.security.keycloak.initial_root_password
    if password:
        print(f"Kubecloak master realm username={username} password={password}")

    print(
        "Additional administration docs can be found at https://docs.nebari.dev/en/stable/source/admin_guide/"
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
        # Note if we used the Pydantic model properly, we might get that nebari_config.prevent_deploy always exists but defaults to False
        raise ValueError(
            textwrap.dedent(
                """
        Deployment prevented due to the prevent_deploy setting in your nebari-config.yaml file.
        You could remove that field to deploy your Nebari, but please do NOT do so without fully understanding why that value was set in the first place.

        It may have been set during an upgrade of your nebari-config.yaml file because we do not believe it is safe to redeploy the new
        version of Nebari without having a full backup of your system ready to restore. It may be known that an in-situ upgrade is impossible
        and that redeployment will tear down your existing infrastructure before creating an entirely new Nebari without your old data.

        PLEASE get in touch with Nebari development team at https://github.com/nebari-dev/nebari for assistance in proceeding.
        Your data may be at risk without our guidance.
        """
            )
        )

    logger.info(f'All nebari endpoints will be under https://{config["domain"]}')

    if disable_checks:
        logger.warning(
            "The validation checks at the end of each stage have been disabled"
        )

    with timer(logger, "deploying Nebari"):
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
