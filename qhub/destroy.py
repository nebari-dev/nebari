import logging

from qhub.utils import timer, check_cloud_credentials
from qhub.provider import terraform
from qhub.state import terraform_state_sync

logger = logging.getLogger(__name__)


def destroy_configuration(config, skip_remote_state_provision=False, full_only=False):
    logger.info(
        """Removing all infrastructure, your local files will still remain,
    you can use 'qhub deploy' to re-install infrastructure using same config file\n"""
    )

    with timer(logger, "destroying QHub"):
        # 01 Check Environment Variables
        check_cloud_credentials(config)

        # 02 Remove all infrastructure
        terraform.init(directory="infrastructure")
        terraform.refresh(directory="infrastructure")

        if not full_only:
            stages = (
                {
                    "name": "General cluster software",
                    "targets": [
                        "module.kubernetes-nfs-mount",
                        "module.kubernetes-nfs-server",
                        "module.kubernetes-nfs-mount",
                        "module.kubernetes-conda-store-server",
                        "module.kubernetes-conda-store-mount",
                        "module.kubernetes-autoscaling",
                        "module.qhub",
                        "module.prefect",
                        "module.monitoring",
                        "module.clearml",
                        "module.forwardauth",
                        "random_password.jupyterhub-jhsecret",
                        "random_password.forwardauth-jhsecret",
                        "kubernetes_secret.qhub_yaml_secret",
                    ]
                    + [
                        f"module.{helmext['name']}-extension"
                        for helmext in config.get("helm_extensions", [])
                    ]
                    + [
                        f"module.ext-{ext['name']}"
                        for ext in config.get("extensions", [])
                    ],
                },
                {
                    "name": "Keycloak Config",
                    "targets": [
                        "module.kubernetes-keycloak-config",
                        "random_password.keycloak-qhub-bot-password",
                    ],
                },
                {
                    "name": "Keycloak Helm installation",
                    "targets": ["module.kubernetes-keycloak-helm"],
                },
                {
                    "name": "Kubernetes Ingress",
                    "targets": ["module.kubernetes-ingress"],
                },
                {
                    "name": "Kubernetes Init",
                    "targets": [
                        "module.kubernetes-initialization",
                    ],
                },
                {
                    "name": "Kubernetes Cluster",
                    "targets": [
                        "module.kubernetes",
                    ],
                },
                {
                    "name": "Cloud Infrastructure",
                    "targets": [
                        "module.registry-jupyterhub",  # GCP
                        "module.efs",  # AWS
                        "module.registry-jupyterlab",  # AWS
                        "module.network",  # AWS
                        "module.accounting",  # AWS
                        "module.registry",  # Azure
                    ],
                },
            )

            for stageinfo in stages:
                logger.info(
                    f"Running Terraform Stage: {stageinfo['name']} {stageinfo['targets']}"
                )
                terraform.destroy(
                    directory="infrastructure", targets=stageinfo["targets"]
                )

        else:
            logger.info("Running Terraform Stage: FULL")
            terraform.destroy(directory="infrastructure")

        # 03 Remove terraform backend remote state bucket
        # backwards compatible with `qhub-config.yaml` which
        # don't have `terraform_state` key
        if (
            (not skip_remote_state_provision)
            and (config.get("terraform_state", {}).get("type", "") == "remote")
            and (config.get("provider") != "local")
        ):
            terraform_state_sync(config)
            terraform.destroy(directory="terraform-state")
