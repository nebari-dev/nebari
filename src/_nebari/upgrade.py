import json
import logging
import re
import secrets
import string
from abc import ABC
from pathlib import Path

import rich
from pydantic.error_wrappers import ValidationError
from rich.prompt import Prompt

from _nebari.config import backup_configuration
from _nebari.utils import (
    get_k8s_version_prefix,
    get_provider_config_block_name,
    load_yaml,
    yaml,
)
from _nebari.version import __version__, rounded_ver_parse
from nebari.schema import ProviderEnum, is_version_accepted

logger = logging.getLogger(__name__)

NEBARI_WORKFLOW_CONTROLLER_DOCS = (
    "https://www.nebari.dev/docs/how-tos/using-argo/#jupyterflow-override-beta"
)
ARGO_JUPYTER_SCHEDULER_REPO = "https://github.com/nebari-dev/argo-jupyter-scheduler"

UPGRADE_KUBERNETES_MESSAGE = "Please see the [green][link=https://www.nebari.dev/docs/how-tos/kubernetes-version-upgrade]Kubernetes upgrade docs[/link][/green] for more information."
DESTRUCTIVE_UPGRADE_WARNING = "-> This version upgrade will result in your cluster being completely torn down and redeployed.  Please ensure you have backed up any data you wish to keep before proceeding!!!"


def do_upgrade(config_filename, attempt_fixes=False):
    config = load_yaml(config_filename)
    if config.get("qhub_version"):
        rich.print(
            f"Your config file [purple]{config_filename}[/purple] uses the deprecated qhub_version key.  Please change qhub_version to nebari_version and re-run the upgrade command."
        )
        return

    try:
        from nebari.plugins import nebari_plugin_manager

        nebari_plugin_manager.read_config(config_filename)
        rich.print(
            f"Your config file [purple]{config_filename}[/purple] appears to be already up-to-date for Nebari version [green]{__version__}[/green]"
        )
        return
    except (ValidationError, ValueError) as e:
        if is_version_accepted(config.get("nebari_version", "")):
            # There is an unrelated validation problem
            rich.print(
                f"Your config file [purple]{config_filename}[/purple] appears to be already up-to-date for Nebari version [green]{__version__}[/green] but there is another validation error.\n"
            )
            raise e

    start_version = config.get("nebari_version", "")

    UpgradeStep.upgrade(
        config, start_version, __version__, config_filename, attempt_fixes
    )

    # Backup old file
    backup_configuration(config_filename, f".{start_version or 'old'}")

    with config_filename.open("wt") as f:
        yaml.dump(config, f)

    rich.print(
        f"Saving new config file [purple]{config_filename}[/purple] ready for Nebari version [green]{__version__}[/green]"
    )

    ci_cd = config.get("ci_cd", {}).get("type", "")
    if ci_cd in ("github-actions", "gitlab-ci"):
        rich.print(
            f"\nSince you are using ci_cd [green]{ci_cd}[/green] you also need to re-render the workflows and re-commit the files to your Git repo:\n"
            f"   nebari render -c [purple]{config_filename}[/purple]\n"
        )


class UpgradeStep(ABC):
    _steps = {}

    version = ""  # Each subclass must have a version - these should be full release versions (not dev/prerelease)

    def __init_subclass__(cls):
        assert cls.version != ""
        assert (
            cls.version not in cls._steps
        )  # Would mean multiple upgrades for the same step
        cls._steps[cls.version] = cls

    @classmethod
    def has_step(cls, version):
        return version in cls._steps

    @classmethod
    def upgrade(
        cls, config, start_version, finish_version, config_filename, attempt_fixes=False
    ):
        """
        Runs through all required upgrade steps (i.e. relevant subclasses of UpgradeStep).
        Calls UpgradeStep.upgrade_step for each.
        """
        starting_ver = rounded_ver_parse(start_version or "0.0.0")
        finish_ver = rounded_ver_parse(finish_version)

        if finish_ver < starting_ver:
            raise ValueError(
                f"Your nebari-config.yaml already belongs to a later version ({start_version}) than the installed version of Nebari ({finish_version}).\n"
                "You should upgrade the installed nebari package (e.g. pip install --upgrade nebari) to work with your deployment."
            )

        step_versions = sorted(
            [
                v
                for v in cls._steps.keys()
                if rounded_ver_parse(v) > starting_ver
                and rounded_ver_parse(v) <= finish_ver
            ],
            key=rounded_ver_parse,
        )

        current_start_version = start_version
        for stepcls in [cls._steps[str(v)] for v in step_versions]:
            step = stepcls()
            config = step.upgrade_step(
                config,
                current_start_version,
                config_filename,
                attempt_fixes=attempt_fixes,
            )
            current_start_version = step.get_version()
            print("\n")

        return config

    def get_version(self):
        return self.version

    def requires_nebari_version_field(self):
        return rounded_ver_parse(self.version) > rounded_ver_parse("0.3.13")

    def upgrade_step(self, config, start_version, config_filename, *args, **kwargs):
        """
        Perform the upgrade from start_version to self.version.

        Generally, this will be in-place in config, but must also return config dict.

        config_filename may be useful to understand the file path for nebari-config.yaml, for example
        to output another file in the same location.

        The standard body here will take care of setting nebari_version and also updating the image tags.

        It should normally be left as-is for all upgrades. Use _version_specific_upgrade below
        for any actions that are only required for the particular upgrade you are creating.
        """
        finish_version = self.get_version()
        __rounded_finish_version__ = ".".join(
            [str(c) for c in rounded_ver_parse(finish_version)]
        )
        rich.print(
            f"\n---> Starting upgrade from [green]{start_version or 'old version'}[/green] to [green]{finish_version}[/green]\n"
        )

        # Set the new version
        if start_version == "":
            assert "nebari_version" not in config
        assert self.version != start_version

        if self.requires_nebari_version_field():
            rich.print(f"Setting nebari_version to [green]{self.version}[/green]")
            config["nebari_version"] = self.version

        def contains_image_and_tag(s: str) -> bool:
            # match on `quay.io/nebari/nebari-<...>:YYYY.MM.XX``
            pattern = r"^quay\.io\/nebari\/nebari-(jupyterhub|jupyterlab|dask-worker)(-gpu)?:\d{4}\.\d+\.\d+$"
            return bool(re.match(pattern, s))

        def replace_image_tag_legacy(image, start_version, new_version):
            start_version_regex = start_version.replace(".", "\\.")
            if not start_version:
                start_version_regex = "0\\.[0-3]\\.[0-9]{1,2}"

            docker_image_regex = re.compile(
                f"^([A-Za-z0-9_-]+/[A-Za-z0-9_-]+):v{start_version_regex}$"
            )

            m = docker_image_regex.match(image)
            if m:
                return ":".join([m.groups()[0], f"v{new_version}"])
            return None

        def replace_image_tag(s: str, new_version: str, config_path: str) -> str:
            legacy_replacement = replace_image_tag_legacy(s, start_version, new_version)
            if legacy_replacement:
                return legacy_replacement

            if not contains_image_and_tag(s):
                return s
            image_name, current_tag = s.split(":")
            if current_tag == new_version:
                return s
            loc = f"{config_path}: {image_name}"
            response = Prompt.ask(
                f"\nDo you want to replace current tag [green]{current_tag}[/green] with [green]{new_version}[/green] for:\n[purple]{loc}[/purple]? [Y/n] ",
                default="Y",
            )
            if response.lower() in ["y", "yes", ""]:
                return s.replace(current_tag, new_version)
            else:
                return s

        def set_nested_item(config: dict, config_path: list, value: str):
            config_path = config_path.split(".")
            for k in config_path[:-1]:
                try:
                    k = int(k)
                except ValueError:
                    pass
                config = config[k]
            try:
                config_path[-1] = int(config_path[-1])
            except ValueError:
                pass
            config[config_path[-1]] = value

        def update_image_tag(config, config_path, current_image, new_version):
            new_image = replace_image_tag(current_image, new_version, config_path)
            if new_image != current_image:
                set_nested_item(config, config_path, new_image)

            return config

        # update default_images
        for k, v in config.get("default_images", {}).items():
            config_path = f"default_images.{k}"
            config = update_image_tag(
                config, config_path, v, __rounded_finish_version__
            )

        # update profiles.jupyterlab images
        for i, v in enumerate(config.get("profiles", {}).get("jupyterlab", [])):
            current_image = v.get("kubespawner_override", {}).get("image", None)
            if current_image:
                config = update_image_tag(
                    config,
                    f"profiles.jupyterlab.{i}.kubespawner_override.image",
                    current_image,
                    __rounded_finish_version__,
                )

        # update profiles.dask_worker images
        for k, v in config.get("profiles", {}).get("dask_worker", {}).items():
            current_image = v.get("image", None)
            if current_image:
                config = update_image_tag(
                    config,
                    f"profiles.dask_worker.{k}.image",
                    current_image,
                    __rounded_finish_version__,
                )

        # Run any version-specific tasks
        return self._version_specific_upgrade(
            config, start_version, config_filename, *args, **kwargs
        )

    def _version_specific_upgrade(
        self, config, start_version, config_filename, *args, **kwargs
    ):
        """
        Override this method in subclasses if you need to do anything specific to your version.
        """
        return config


class Upgrade_0_3_12(UpgradeStep):
    version = "0.3.12"

    def _version_specific_upgrade(
        self, config, start_version, config_filename, *args, **kwargs
    ):
        """
        This version of Nebari requires a conda_store image for the first time.
        """
        if config.get("default_images", {}).get("conda_store", None) is None:
            newimage = "quansight/conda-store-server:v0.3.3"
            rich.print(
                f"Adding default_images: conda_store image as [green]{newimage}[/green]"
            )
            if "default_images" not in config:
                config["default_images"] = {}
            config["default_images"]["conda_store"] = newimage
        return config


class Upgrade_0_4_0(UpgradeStep):
    version = "0.4.0"

    def _version_specific_upgrade(
        self, config, start_version, config_filename: Path, *args, **kwargs
    ):
        """
        Upgrade to Keycloak.
        """
        security = config.get("security", {})
        users = security.get("users", {})
        groups = security.get("groups", {})

        # Custom Authenticators are no longer allowed
        if (
            config.get("security", {}).get("authentication", {}).get("type", "")
            == "custom"
        ):
            customauth_warning = (
                f"Custom Authenticators are no longer supported in {self.version} because Keycloak "
                "manages all authentication.\nYou need to find a way to support your authentication "
                "requirements within Keycloak."
            )
            if not kwargs.get("attempt_fixes", False):
                raise ValueError(
                    f"{customauth_warning}\n\nRun `nebari upgrade --attempt-fixes` to switch to basic Keycloak authentication instead."
                )
            else:
                rich.print(f"\nWARNING: {customauth_warning}")
                rich.print(
                    "\nSwitching to basic Keycloak authentication instead since you specified --attempt-fixes."
                )
                config["security"]["authentication"] = {"type": "password"}

        # Create a group/user import file for Keycloak

        realm_import_filename = config_filename.parent / "nebari-users-import.json"

        realm = {"id": "nebari", "realm": "nebari"}
        realm["users"] = [
            {
                "username": k,
                "enabled": True,
                "groups": sorted(
                    list(
                        (
                            {v.get("primary_group", "")}
                            | set(v.get("secondary_groups", []))
                        )
                        - {""}
                    )
                ),
            }
            for k, v in users.items()
        ]
        realm["groups"] = [
            {"name": k, "path": f"/{k}"}
            for k, v in groups.items()
            if k not in {"users", "admin"}
        ]

        backup_configuration(realm_import_filename)

        with realm_import_filename.open("wt") as f:
            json.dump(realm, f, indent=2)

        rich.print(
            f"\nSaving user/group import file [purple]{realm_import_filename}[/purple].\n\n"
            "ACTION REQUIRED: You must import this file into the Keycloak admin webpage after you redeploy Nebari.\n"
            "Visit the URL path /auth/ and login as 'root'. Under Manage, click Import and select this file.\n\n"
            "Non-admin users will default to analyst group membership after the upgrade (no dask access), "
            "so you may wish to promote some users into the developer group.\n"
        )

        if "users" in security:
            del security["users"]
        if "groups" in security:
            if "users" in security["groups"]:
                # Ensure the users default group is added to Keycloak
                security["shared_users_group"] = True
            del security["groups"]

        if "terraform_modules" in config:
            del config["terraform_modules"]
            rich.print(
                "Removing terraform_modules field from config as it is no longer used.\n"
            )

        if "default_images" not in config:
            config["default_images"] = {}

        # Remove conda_store image from default_images
        if "conda_store" in config["default_images"]:
            del config["default_images"]["conda_store"]

        # Remove dask_gateway image from default_images
        if "dask_gateway" in config["default_images"]:
            del config["default_images"]["dask_gateway"]

        # Create root password
        default_password = "".join(
            secrets.choice(string.ascii_letters + string.digits) for i in range(16)
        )
        security.setdefault("keycloak", {})["initial_root_password"] = default_password

        rich.print(
            f"Generated default random password=[green]{default_password}[/green] for Keycloak root user (Please change at /auth/ URL path).\n"
        )

        # project was never needed in Azure - it remained as PLACEHOLDER in earlier nebari inits!
        if "azure" in config:
            if "project" in config["azure"]:
                del config["azure"]["project"]

        # "oauth_callback_url" and "scope" not required in nebari-config.yaml
        # for Auth0 and Github authentication
        auth_config = config["security"]["authentication"].get("config", None)
        if auth_config:
            if "oauth_callback_url" in auth_config:
                del auth_config["oauth_callback_url"]
            if "scope" in auth_config:
                del auth_config["scope"]

        # It is not safe to immediately redeploy without backing up data ready to restore data
        # since a new cluster will be created for the new version.
        # Setting the following flag will prevent deployment and display guidance to the user
        # which they can override if they are happy they understand the situation.
        config["prevent_deploy"] = True

        return config


class Upgrade_0_4_1(UpgradeStep):
    version = "0.4.1"

    def _version_specific_upgrade(
        self, config, start_version, config_filename: Path, *args, **kwargs
    ):
        """
        Upgrade jupyterlab profiles.
        """
        rich.print("\nUpgrading jupyterlab profiles in order to specify access type:\n")

        profiles_jupyterlab = config.get("profiles", {}).get("jupyterlab", [])
        for profile in profiles_jupyterlab:
            name = profile.get("display_name", "")

            if "groups" in profile or "users" in profile:
                profile["access"] = "yaml"
            else:
                profile["access"] = "all"

            rich.print(
                f"Setting access type of JupyterLab profile [green]{name}[/green] to [green]{profile['access']}[/green]"
            )
        return config


class Upgrade_2023_4_2(UpgradeStep):
    version = "2023.4.2"

    def _version_specific_upgrade(
        self, config, start_version, config_filename: Path, *args, **kwargs
    ):
        """
        Prompt users to delete Argo CRDs
        """

        kubectl_delete_argo_crds_cmd = "kubectl delete crds clusterworkflowtemplates.argoproj.io cronworkflows.argoproj.io workfloweventbindings.argoproj.io workflows.argoproj.io workflowtasksets.argoproj.io workflowtemplates.argoproj.io"

        kubectl_delete_argo_sa_cmd = (
            f"kubectl delete sa -n {config['namespace']} argo-admin argo-dev argo-view"
        )

        rich.print(
            f"\n\n[bold cyan]Note:[/] Upgrading requires a one-time manual deletion of the Argo Workflows Custom Resource Definitions (CRDs) and service accounts. \n\n[red bold]Warning:  [link=https://{config['domain']}/argo/workflows]Workflows[/link] and [link=https://{config['domain']}/argo/workflows]CronWorkflows[/link] created before deleting the CRDs will be erased when the CRDs are deleted and will not be restored.[/red bold] \n\nThe updated CRDs will be installed during the next [cyan bold]nebari deploy[/cyan bold] step. Argo Workflows will not function after deleting the CRDs until the updated CRDs and service accounts are installed in the next nebari deploy. You must delete the Argo Workflows CRDs and service accounts before upgrading to {self.version} (or later) or the deploy step will fail.  Please delete them before proceeding by generating a kubeconfig (see [link=https://www.nebari.dev/docs/how-tos/debug-nebari/#generating-the-kubeconfig]docs[/link]), installing kubectl (see [link=https://www.nebari.dev/docs/how-tos/debug-nebari#installing-kubectl]docs[/link]), and running the following two commands:\n\n\t[cyan bold]{kubectl_delete_argo_crds_cmd} [/cyan bold]\n\n\t[cyan bold]{kubectl_delete_argo_sa_cmd} [/cyan bold]"
            ""
        )

        continue_ = Prompt.ask(
            "Have you deleted the Argo Workflows CRDs and service accounts? [y/N] ",
            default="N",
        )
        if not continue_ == "y":
            rich.print(
                f"You must delete the Argo Workflows CRDs and service accounts before upgrading to [green]{self.version}[/green] (or later)."
            )
            exit()

        return config


class Upgrade_2023_7_1(UpgradeStep):
    version = "2023.7.1"

    def _version_specific_upgrade(
        self, config, start_version, config_filename: Path, *args, **kwargs
    ):
        provider = config["provider"]
        if provider == ProviderEnum.aws.value:
            rich.print("\n ⚠️  DANGER ⚠️")
            rich.print(
                DESTRUCTIVE_UPGRADE_WARNING,
                "The 'prevent_deploy' flag has been set in your config file and must be manually removed to deploy.",
            )
            config["prevent_deploy"] = True

        return config


class Upgrade_2023_7_2(UpgradeStep):
    version = "2023.7.2"

    def _version_specific_upgrade(
        self, config, start_version, config_filename: Path, *args, **kwargs
    ):
        argo = config.get("argo_workflows", {})
        if argo.get("enabled"):
            response = Prompt.ask(
                f"\nDo you want to enable the [green][link={NEBARI_WORKFLOW_CONTROLLER_DOCS}]Nebari Workflow Controller[/link][/green], required for [green][link={ARGO_JUPYTER_SCHEDULER_REPO}]Argo-Jupyter-Scheduler[/link][green]? [Y/n] ",
                default="Y",
            )
            if response.lower() in ["y", "yes", ""]:
                argo["nebari_workflow_controller"] = {"enabled": True}

        rich.print("\n ⚠️ Deprecation Warnings ⚠️")
        rich.print(
            f"-> [green]{self.version}[/green] is the last Nebari version that supports CDS Dashboards"
        )

        return config


class Upgrade_2023_10_1(UpgradeStep):
    version = "2023.10.1"
    # JupyterHub Helm chart 2.0.0 (app version 3.0.0) requires K8S Version >=1.23. (reference: https://z2jh.jupyter.org/en/stable/)
    # This released has been tested against 1.26
    min_k8s_version = 1.26

    def _version_specific_upgrade(
        self, config, start_version, config_filename: Path, *args, **kwargs
    ):
        # Upgrading to 2023.10.1 is considered high-risk because it includes a major refacto
        # to introduce the extension mechanism system.
        rich.print("\n ⚠️  Warning ⚠️")
        rich.print(
            f"-> Nebari version [green]{self.version}[/green] includes a major refactor to introduce an extension mechanism that supports the development of third-party plugins."
        )
        rich.print(
            "-> Data should be backed up before performing this upgrade ([green][link=https://www.nebari.dev/docs/how-tos/manual-backup]see docs[/link][/green])  The 'prevent_deploy' flag has been set in your config file and must be manually removed to deploy."
        )
        rich.print(
            "-> Please also run the [green]rm -rf stages[/green] so that we can regenerate an updated set of Terraform scripts for your deployment."
        )

        # Setting the following flag will prevent deployment and display guidance to the user
        # which they can override if they are happy they understand the situation.
        config["prevent_deploy"] = True

        # Nebari version 2023.10.1 upgrades JupyterHub to 3.1.  CDS Dashboards are only compatible with
        # JupyterHub versions 1.X and so will be removed during upgrade.
        rich.print("\n ⚠️  Deprecation Warning ⚠️")
        rich.print(
            f"-> CDS dashboards are no longer supported in Nebari version [green]{self.version}[/green] and will be uninstalled."
        )
        if config.get("cdsdashboards"):
            rich.print("-> Removing cdsdashboards from config file.")
            del config["cdsdashboards"]

        # Deprecation Warning - ClearML, Prefect, kbatch
        rich.print("\n ⚠️  Deprecation Warning ⚠️")
        rich.print(
            "-> We will be removing and ending support for ClearML, Prefect and kbatch in the next release. The kbatch has been functionally replaced by Argo-Jupyter-Scheduler. We have seen little interest in ClearML and Prefect in recent years, and removing makes sense at this point. However if you wish to continue using them with Nebari we encourage you to [green][link=https://www.nebari.dev/docs/how-tos/nebari-extension-system/#developing-an-extension]write your own Nebari extension[/link][/green]."
        )

        # Kubernetes version check
        # JupyterHub Helm chart 2.0.0 (app version 3.0.0) requires K8S Version >=1.23. (reference: https://z2jh.jupyter.org/en/stable/)

        provider = config["provider"]
        provider_config_block = get_provider_config_block_name(provider)

        # Get current Kubernetes version if available in config.
        current_version = config.get(provider_config_block, {}).get(
            "kubernetes_version", None
        )

        # Convert to decimal prefix
        if provider in ["aws", "azure", "gcp", "do"]:
            current_version = get_k8s_version_prefix(current_version)

        # Try to convert known Kubernetes versions to float.
        if current_version is not None:
            try:
                current_version = float(current_version)
            except ValueError:
                current_version = None

        # Handle checks for when Kubernetes version should be detectable
        if provider in ["aws", "azure", "gcp", "do"]:
            # Kubernetes version not found in provider block
            if current_version is None:
                rich.print("\n ⚠️  Warning ⚠️")
                rich.print(
                    f"-> Unable to detect Kubernetes version for provider {provider}.  Nebari version [green]{self.version}[/green] requires Kubernetes version {str(self.min_k8s_version)}.  Please confirm your Kubernetes version is configured before upgrading."
                )

            # Kubernetes version less than required minimum
            if (
                isinstance(current_version, float)
                and current_version < self.min_k8s_version
            ):
                rich.print("\n ⚠️  Warning ⚠️")
                rich.print(
                    f"-> Nebari version [green]{self.version}[/green] requires Kubernetes version {str(self.min_k8s_version)}.  Your configured Kubernetes version is [red]{current_version}[/red]. {UPGRADE_KUBERNETES_MESSAGE}"
                )
                version_diff = round(self.min_k8s_version - current_version, 2)
                if version_diff > 0.01:
                    rich.print(
                        "-> The Kubernetes version is multiple minor versions behind the minimum required version. You will need to perform the upgrade one minor version at a time.  For example, if your current version is 1.24, you will need to upgrade to 1.25, and then 1.26."
                    )
                rich.print(
                    f"-> Update the value of [green]{provider_config_block}.kubernetes_version[/green] in your config file to a newer version of Kubernetes and redeploy."
                )

        else:
            rich.print("\n ⚠️  Warning ⚠️")
            rich.print(
                f"-> Unable to detect Kubernetes version for provider {provider}.  Nebari version [green]{self.version}[/green] requires Kubernetes version {str(self.min_k8s_version)} or greater."
            )
            rich.print(
                "-> Please ensure your Kubernetes version is up-to-date before proceeding."
            )

        if provider == "aws":
            rich.print("\n ⚠️  DANGER ⚠️")
            rich.print(DESTRUCTIVE_UPGRADE_WARNING)

        return config


__rounded_version__ = ".".join([str(c) for c in rounded_ver_parse(__version__)])

# Manually-added upgrade steps must go above this line
if not UpgradeStep.has_step(__rounded_version__):
    # Always have a way to upgrade to the latest full version number, even if no customizations
    # Don't let dev/prerelease versions cloud things
    class UpgradeLatest(UpgradeStep):
        version = __rounded_version__
