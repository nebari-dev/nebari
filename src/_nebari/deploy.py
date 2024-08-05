import contextlib
import logging
import pathlib
import textwrap
from typing import Any, Dict, List

from _nebari.utils import timer
from nebari import hookspecs, schema

logger = logging.getLogger(__name__)


def deploy_configuration(
    config: schema.Main,
    stages: List[hookspecs.NebariStage],
    disable_prompt: bool = False,
    disable_checks: bool = False,
) -> Dict[str, Any]:
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

    if config.domain is None:
        logger.info(
            "All nebari endpoints will be under kubernetes load balancer address which cannot be known before deployment"
        )
    else:
        logger.info(f"All nebari endpoints will be under https://{config.domain}")

    if disable_checks:
        logger.warning(
            "The validation checks at the end of each stage have been disabled"
        )

    with timer(logger, "deploying Nebari"):
        stage_outputs = {}
        with contextlib.ExitStack() as stack:
            for stage in stages:
                s: hookspecs.NebariStage = stage(
                    output_directory=pathlib.Path.cwd(), config=config
                )
                stack.enter_context(s.deploy(stage_outputs, disable_prompt))

                if not disable_checks:
                    s.check(stage_outputs, disable_prompt)
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
            "Additional administration docs can be found at https://www.nebari.dev/docs/how-tos/configuring-keycloak"
        )

    return stage_outputs
