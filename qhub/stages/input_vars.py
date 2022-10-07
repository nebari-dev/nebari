import json
import os
import tempfile
from urllib.parse import urlencode

from qhub.constants import DEFAULT_CONDA_STORE_IMAGE_TAG


def stage_01_terraform_state(stage_outputs, config):
    if config["provider"] == "do":
        return {
            "name": config["project_name"],
            "namespace": config["namespace"],
            "region": config["digital_ocean"]["region"],
        }
    elif config["provider"] == "gcp":
        return {
            "name": config["project_name"],
            "namespace": config["namespace"],
            "region": config["google_cloud_platform"]["region"],
        }
    elif config["provider"] == "aws":
        return {
            "name": config["project_name"],
            "namespace": config["namespace"],
        }
    elif config["provider"] == "azure":
        return {
            "name": config["project_name"],
            "namespace": config["namespace"],
            "region": config["azure"]["region"],
            "storage_account_postfix": config["azure"]["storage_account_postfix"],
            "state_resource_group_name": f'{config["project_name"]}-{config["namespace"]}-state',
        }
    else:
        return {}


def stage_02_infrastructure(stage_outputs, config):
    if config["provider"] == "local":
        return {
            "kubeconfig_filename": os.path.join(
                tempfile.gettempdir(), "QHUB_KUBECONFIG"
            ),
            "kube_context": config["local"].get("kube_context"),
        }
    elif config["provider"] == "existing":
        return {"kube_context": config["existing"].get("kube_context")}
    elif config["provider"] == "do":
        return {
            "name": config["project_name"],
            "environment": config["namespace"],
            "region": config["digital_ocean"]["region"],
            "kubernetes_version": config["digital_ocean"]["kubernetes_version"],
            "node_groups": config["digital_ocean"]["node_groups"],
            "kubeconfig_filename": os.path.join(
                tempfile.gettempdir(), "QHUB_KUBECONFIG"
            ),
            **config.get("do", {}).get("terraform_overrides", {}),
        }
    elif config["provider"] == "gcp":
        return {
            "name": config["project_name"],
            "environment": config["namespace"],
            "region": config["google_cloud_platform"]["region"],
            "project_id": config["google_cloud_platform"]["project"],
            "node_groups": [
                {
                    "name": key,
                    "instance_type": value["instance"],
                    "min_size": value["min_nodes"],
                    "max_size": value["max_nodes"],
                    "guest_accelerators": value["guest_accelerators"]
                    if "guest_accelerators" in value
                    else [],
                    **value,
                }
                for key, value in config["google_cloud_platform"]["node_groups"].items()
            ],
            "kubeconfig_filename": os.path.join(
                tempfile.gettempdir(), "QHUB_KUBECONFIG"
            ),
            **config.get("gcp", {}).get("terraform_overrides", {}),
        }
    elif config["provider"] == "azure":
        return {
            "name": config["project_name"],
            "environment": config["namespace"],
            "region": config["azure"]["region"],
            "kubernetes_version": config["azure"]["kubernetes_version"],
            "node_groups": config["azure"]["node_groups"],
            "kubeconfig_filename": os.path.join(
                tempfile.gettempdir(), "QHUB_KUBECONFIG"
            ),
            "resource_group_name": f'{config["project_name"]}-{config["namespace"]}',
            "node_resource_group_name": f'{config["project_name"]}-{config["namespace"]}-node-resource-group',
            **config.get("azure", {}).get("terraform_overrides", {}),
        }
    elif config["provider"] == "aws":
        return {
            "name": config["project_name"],
            "environment": config["namespace"],
            "node_groups": [
                {
                    "name": key,
                    "min_size": value["min_nodes"],
                    "desired_size": max(value["min_nodes"], 1),
                    "max_size": value["max_nodes"],
                    "gpu": value.get("gpu", False),
                    "instance_type": value["instance"],
                }
                for key, value in config["amazon_web_services"]["node_groups"].items()
            ],
            "kubeconfig_filename": os.path.join(
                tempfile.gettempdir(), "QHUB_KUBECONFIG"
            ),
            **config.get("aws", {}).get("terraform_overrides", {}),
        }
    else:
        return {}


def stage_03_kubernetes_initialize(stage_outputs, config):
    if config["provider"] == "gcp":
        gpu_enabled = any(
            node_group.get("guest_accelerators")
            for node_group in config["google_cloud_platform"]["node_groups"].values()
        )
        gpu_node_group_names = []

    elif config["provider"] == "aws":
        gpu_enabled = any(
            node_group.get("gpu")
            for node_group in config["amazon_web_services"]["node_groups"].values()
        )
        gpu_node_group_names = [
            group for group in config["amazon_web_services"]["node_groups"].keys()
        ]
    else:
        gpu_enabled = False
        gpu_node_group_names = []

    return {
        "name": config["project_name"],
        "environment": config["namespace"],
        "cloud-provider": config["provider"],
        "aws-region": config.get("amazon_web_services", {}).get("region"),
        "external_container_reg": config.get(
            "external_container_reg", {"enabled": False}
        ),
        "gpu_enabled": gpu_enabled,
        "gpu_node_group_names": gpu_node_group_names,
    }


def _calculate_note_groups(config):
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
    elif config["provider"] == "existing":
        return config["existing"].get("node_selectors")
    else:
        return config["local"]["node_selectors"]


def stage_04_kubernetes_ingress(stage_outputs, config):
    cert_type = config["certificate"]["type"]
    cert_details = {"certificate-service": cert_type}
    if cert_type == "lets-encrypt":
        cert_details["acme-email"] = config["certificate"]["acme_email"]
        cert_details["acme-server"] = config["certificate"]["acme_server"]

    return {
        **{
            "name": config["project_name"],
            "environment": config["namespace"],
            "node_groups": _calculate_note_groups(config),
            **config.get("ingress", {}).get("terraform_overrides", {}),
        },
        **cert_details,
    }


def stage_05_kubernetes_keycloak(stage_outputs, config):
    initial_root_password = (
        config["security"].get("keycloak", {}).get("initial_root_password", "")
    )
    if initial_root_password is None:
        initial_root_password = ""

    return {
        "name": config["project_name"],
        "environment": config["namespace"],
        "endpoint": config["domain"],
        "initial-root-password": initial_root_password,
        "overrides": [
            json.dumps(config["security"].get("keycloak", {}).get("overrides", {}))
        ],
        "node-group": _calculate_note_groups(config)["general"],
    }


def stage_06_kubernetes_keycloak_configuration(stage_outputs, config):
    realm_id = "qhub"

    users_group = (
        ["users"] if config["security"].get("shared_users_group", False) else []
    )

    return {
        "realm": realm_id,
        "realm_display_name": config["security"]
        .get("keycloak", {})
        .get("realm_display_name", realm_id),
        "authentication": config["security"]["authentication"],
        "keycloak_groups": ["admin", "developer", "analyst"] + users_group,
        "default_groups": ["analyst"] + users_group,
    }


def _split_docker_image_name(image_name):
    name, tag = image_name.split(":")
    return {"name": name, "tag": tag}


def stage_07_kubernetes_services(stage_outputs, config):
    final_logout_uri = f"https://{config['domain']}/hub/login"

    # Compound any logout URLs from extensions so they are are logged out in succession
    # when Keycloak and JupyterHub are logged out
    for ext in config.get("tf_extensions", []):
        if ext.get("logout", "") != "":
            final_logout_uri = "{}?{}".format(
                f"https://{config['domain']}/{ext['urlslug']}{ext['logout']}",
                urlencode({"redirect_uri": final_logout_uri}),
            )
    jupyterhub_theme = config["theme"]["jupyterhub"]
    if config["theme"]["jupyterhub"].get("display_version") and (
        not config["theme"]["jupyterhub"].get("version", False)
    ):
        jupyterhub_theme.update({"version": f"v{config['qhub_version']}"})

    return {
        "name": config["project_name"],
        "environment": config["namespace"],
        "endpoint": config["domain"],
        "realm_id": stage_outputs["stages/06-kubernetes-keycloak-configuration"][
            "realm_id"
        ]["value"],
        "node_groups": _calculate_note_groups(config),
        # conda-store
        "conda-store-environments": config["environments"],
        "conda-store-filesystem-storage": config["storage"]["conda_store"],
        "conda-store-service-token-scopes": {
            "cdsdashboards": {
                "primary_namespace": "cdsdashboards",
                "role_bindings": {
                    "*/*": ["viewer"],
                },
            }
        },
        "conda-store-extra-settings": config.get("conda_store", {}).get(
            "extra_settings", {}
        ),
        "conda-store-extra-config": config.get("conda_store", {}).get(
            "extra_config", ""
        ),
        "conda-store-image-tag": config.get("conda-store", {}).get(
            "image_tag", DEFAULT_CONDA_STORE_IMAGE_TAG
        ),
        # jupyterhub
        "cdsdashboards": config["cdsdashboards"],
        "jupyterhub-theme": jupyterhub_theme,
        "jupyterhub-image": _split_docker_image_name(
            config["default_images"]["jupyterhub"]
        ),
        "jupyterhub-shared-storage": config["storage"]["shared_filesystem"],
        "jupyterhub-shared-endpoint": stage_outputs["stages/02-infrastructure"]
        .get("nfs_endpoint", {})
        .get("value"),
        "jupyterlab-profiles": config["profiles"]["jupyterlab"],
        "jupyterlab-image": _split_docker_image_name(
            config["default_images"]["jupyterlab"]
        ),
        "jupyterhub-overrides": [
            json.dumps(config.get("jupyterhub", {}).get("overrides", {}))
        ],
        "jupyterhub-hub-extraEnv": json.dumps(
            config.get("jupyterhub", {})
            .get("overrides", {})
            .get("hub", {})
            .get("extraEnv", [])
        ),
        # dask-gateway
        "dask-worker-image": _split_docker_image_name(
            config["default_images"]["dask_worker"]
        ),
        "dask-gateway-profiles": config["profiles"]["dask_worker"],
        # monitoring
        "monitoring-enabled": config["monitoring"]["enabled"],
        # argo-worfklows
        "argo-workflows-enabled": config["argo_workflows"]["enabled"],
        "argo-workflows-overrides": [
            json.dumps(config.get("argo_workflows", {}).get("overrides", {}))
        ],
        # kbatch
        "kbatch-enabled": config["kbatch"]["enabled"],
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
        "clearml-overrides": [
            json.dumps(config.get("clearml", {}).get("overrides", {}))
        ],
        "jupyterhub-logout-redirect-url": final_logout_uri,
    }


def stage_08_qhub_tf_extensions(stage_outputs, config):
    return {
        "environment": config["namespace"],
        "endpoint": config["domain"],
        "realm_id": stage_outputs["stages/06-kubernetes-keycloak-configuration"][
            "realm_id"
        ]["value"],
        "tf_extensions": config.get("tf_extensions", []),
        "qhub_config_yaml": config,
        "keycloak_qhub_bot_password": stage_outputs["stages/05-kubernetes-keycloak"][
            "keycloak_qhub_bot_password"
        ]["value"],
        "helm_extensions": config.get("helm_extensions", []),
    }
