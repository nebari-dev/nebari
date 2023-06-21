import contextlib
import logging
import pathlib
import subprocess
import textwrap

from _nebari.utils import timer
from nebari import schema
from nebari.plugins import get_available_stages

logger = logging.getLogger(__name__)


def guided_install(
    config: schema.Main,
    dns_provider,
    dns_auto_provision,
    disable_prompt=False,
    disable_checks=False,
    skip_remote_state_provision=False,
):
    stage_outputs = {}
    with contextlib.ExitStack() as stack:
        for stage in get_available_stages():
            s = stage(output_directory=pathlib.Path("."), config=config)
            stack.enter_context(s.deploy(stage_outputs))

            if not disable_checks:
                s.check(stage_outputs)
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
    config: schema.Main,
    dns_provider,
    dns_auto_provision,
    disable_prompt,
    disable_checks,
    skip_remote_state_provision,
):
    if config.prevent_deploy:
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

    logger.info(f"All nebari endpoints will be under https://{config.domain}")

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
