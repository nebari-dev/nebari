import functools
import logging
import os

from qhub.provider import terraform
from qhub.stages import input_vars, state_imports
from qhub.utils import (
    check_cloud_credentials,
    keycloak_provider_context,
    kubernetes_provider_context,
    timer,
)

logger = logging.getLogger(__name__)


def gather_stage_outputs(config):
    stage_outputs = {}

    _terraform_init_output = functools.partial(
        terraform.deploy,
        terraform_init=True,
        terraform_import=True,
        terraform_apply=False,
        terraform_destroy=False,
    )

    if (
        config["provider"] not in {"existing", "local"}
        and config["terraform_state"]["type"] == "remote"
    ):
        stage_outputs["stages/01-terraform-state"] = _terraform_init_output(
            directory=os.path.join("stages/01-terraform-state", config["provider"]),
            input_vars=input_vars.stage_01_terraform_state(stage_outputs, config),
            state_imports=state_imports.stage_01_terraform_state(stage_outputs, config),
        )

    stage_outputs["stages/02-infrastructure"] = _terraform_init_output(
        directory=os.path.join("stages/02-infrastructure", config["provider"]),
        input_vars=input_vars.stage_02_infrastructure(stage_outputs, config),
    )

    stage_outputs["stages/03-kubernetes-initialize"] = _terraform_init_output(
        directory="stages/03-kubernetes-initialize",
        input_vars=input_vars.stage_03_kubernetes_initialize(stage_outputs, config),
    )

    stage_outputs["stages/04-kubernetes-ingress"] = _terraform_init_output(
        directory="stages/04-kubernetes-ingress",
        input_vars=input_vars.stage_04_kubernetes_ingress(stage_outputs, config),
    )

    stage_outputs["stages/05-kubernetes-keycloak"] = _terraform_init_output(
        directory="stages/05-kubernetes-keycloak",
        input_vars=input_vars.stage_05_kubernetes_keycloak(stage_outputs, config),
    )

    stage_outputs[
        "stages/06-kubernetes-keycloak-configuration"
    ] = _terraform_init_output(
        directory="stages/06-kubernetes-keycloak-configuration",
        input_vars=input_vars.stage_06_kubernetes_keycloak_configuration(
            stage_outputs, config
        ),
    )

    stage_outputs["stages/07-kubernetes-services"] = _terraform_init_output(
        directory="stages/07-kubernetes-services",
        input_vars=input_vars.stage_07_kubernetes_services(stage_outputs, config),
    )

    stage_outputs["stages/08-qhub-tf-extensions"] = _terraform_init_output(
        directory="stages/08-qhub-tf-extensions",
        input_vars=input_vars.stage_08_qhub_tf_extensions(stage_outputs, config),
    )

    return stage_outputs


def destroy_stages(stage_outputs, config):
    def _terraform_destroy(ignore_errors=False, terraform_apply=False, **kwargs):
        try:
            terraform.deploy(
                terraform_init=True,
                terraform_import=True,
                terraform_apply=terraform_apply,
                terraform_destroy=True,
                **kwargs,
            )
        except terraform.TerraformException as e:
            if not ignore_errors:
                raise e
            return False
        return True

    status = {}

    with kubernetes_provider_context(
        stage_outputs["stages/02-infrastructure"]["kubernetes_credentials"]["value"]
    ):
        with keycloak_provider_context(
            stage_outputs["stages/05-kubernetes-keycloak"]["keycloak_credentials"][
                "value"
            ]
        ):
            status["stages/08-qhub-tf-extensions"] = _terraform_destroy(
                directory="stages/08-qhub-tf-extensions",
                input_vars=input_vars.stage_08_qhub_tf_extensions(
                    stage_outputs, config
                ),
                ignore_errors=True,
            )

            status["stages/07-kubernetes-services"] = _terraform_destroy(
                directory="stages/07-kubernetes-services",
                input_vars=input_vars.stage_07_kubernetes_services(
                    stage_outputs, config
                ),
                ignore_errors=True,
            )

            status["stages/06-kubernetes-keycloak-configuration"] = _terraform_destroy(
                directory="stages/06-kubernetes-keycloak-configuration",
                input_vars=input_vars.stage_06_kubernetes_keycloak_configuration(
                    stage_outputs, config
                ),
                ignore_errors=True,
            )

        status["stages/05-kubernetes-keycloak"] = _terraform_destroy(
            directory="stages/05-kubernetes-keycloak",
            input_vars=input_vars.stage_05_kubernetes_keycloak(stage_outputs, config),
            ignore_errors=True,
        )

        status["stages/04-kubernetes-ingress"] = _terraform_destroy(
            directory="stages/04-kubernetes-ingress",
            input_vars=input_vars.stage_04_kubernetes_ingress(stage_outputs, config),
            ignore_errors=True,
        )

        status["stages/03-kubernetes-initialize"] = _terraform_destroy(
            directory="stages/03-kubernetes-initialize",
            input_vars=input_vars.stage_03_kubernetes_initialize(stage_outputs, config),
            ignore_errors=True,
        )

    status["stages/02-infrastructure"] = _terraform_destroy(
        directory=os.path.join("stages/02-infrastructure", config["provider"]),
        input_vars=input_vars.stage_02_infrastructure(stage_outputs, config),
        ignore_errors=True,
    )

    if (
        config["provider"] not in {"existing", "local"}
        and config["terraform_state"]["type"] == "remote"
    ):
        status["stages/01-terraform-state"] = _terraform_destroy(
            # acl and force_destroy do not import properly
            # and only get refreshed properly with an apply
            terraform_apply=True,
            directory=os.path.join("stages/01-terraform-state", config["provider"]),
            input_vars=input_vars.stage_01_terraform_state(stage_outputs, config),
            ignore_errors=True,
        )

    return status


def destroy_configuration(config):
    logger.info(
        """Removing all infrastructure, your local files will still remain,
    you can use 'qhub deploy' to re-install infrastructure using same config file\n"""
    )
    check_cloud_credentials(config)

    # Populate stage_outputs to determine progress of deployment and
    # get credentials to kubernetes and keycloak context
    stage_outputs = gather_stage_outputs(config)

    with timer(logger, "destroying QHub"):
        status = destroy_stages(stage_outputs, config)

    for stage_name, success in status.items():
        if not success:
            logger.error(f"Stage={stage_name} failed to fully destroy")

    if not all(status.values()):
        logger.error(
            "ERROR: not all qhub stages were destroyed properly. For cloud deployments of QHub typically only stages 01 and 02 need to succeed to properly destroy everything"
        )
    else:
        print("QHub properly destroyed all resources without error")
