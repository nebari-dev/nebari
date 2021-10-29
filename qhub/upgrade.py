import logging
from ruamel import yaml
from abc import ABC
import pathlib
import re

from packaging.version import parse as ver_parse

from pydantic.error_wrappers import ValidationError

from qhub.schema import verify

from .version import __version__

logger = logging.getLogger(__name__)


def do_upgrade(config_filename):

    with config_filename.open() as f:
        config = yaml.safe_load(f)

    try:
        verify(config)
        print(
            f"Your config file {config_filename} appears to be already up-to-date for qhub version {__version__}"
        )
        return
    except (ValidationError, ValueError) as e:
        if config.get("qhub_version", "") == __version__:
            # There is an unrelated validation problem
            print(
                f"Your config file {config_filename} appears to be already up-to-date for qhub version {__version__} but there is another validation error.\n"
            )
            raise e

    start_version = config.get("qhub_version", "")

    UpgradeStep.upgrade(config, start_version, __version__)

    # Backup old file
    backup_filename = pathlib.Path(f"{config_filename}.{start_version or 'old'}.backup")

    if backup_filename.exists():
        i = 1
        while True:
            next_backup_filename = pathlib.Path(f"{backup_filename}~{i}")
            if not next_backup_filename.exists():
                backup_filename = next_backup_filename
                break
            i = i + 1

    config_filename.rename(backup_filename)
    print(f"Backing up old config in {backup_filename}")

    with config_filename.open("wt") as f:
        yaml.dump(config, f, default_flow_style=False, Dumper=yaml.RoundTripDumper)

    print(
        f"Saving new config file {config_filename} ready for QHub version {__version__}"
    )

    ci_cd = config.get("ci_cd", {}).get("type", "")
    if ci_cd in ("github-actions", "gitlab-ci"):
        print(
            f"\nSince you are using ci_cd {ci_cd} you also need to re-render the workflows and re-commit the files to your Git repo:\n"
            f"   qhub render -c {config_filename}\n"
        )


class UpgradeStep(ABC):
    _steps = {}

    version = ""  # Each subclass must have a version

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
    def upgrade(cls, config, start_version, finish_version):
        starting_ver = ver_parse(start_version)
        finish_ver = ver_parse(finish_version)
        step_versions = sorted(
            [
                v
                for v in cls._steps.keys()
                if ver_parse(v) > starting_ver and ver_parse(v) <= finish_ver
            ],
            key=ver_parse,
        )

        current_start_version = start_version
        for stepcls in [cls._steps[str(v)] for v in step_versions]:
            step = stepcls()
            config = step.upgrade_step(config, current_start_version)
            current_start_version = step.get_version()
            print("\n")

        return config

    def get_version(self):
        return self.version

    def requires_qhub_version_field(self):
        return ver_parse(self.version) > ver_parse("0.3.13")

    def upgrade_step(self, config, start_version):

        finish_version = self.get_version()

        print(
            f"\n---> Starting upgrade from {start_version or 'very old version'} to {finish_version}\n"
        )

        # Set the new version
        if start_version == "":
            assert "qhub_version" not in config
        assert self.version != start_version

        if self.requires_qhub_version_field():
            print(f"Setting qhub_version to {self.version}")
            config["qhub_version"] = self.version

        # Update images
        start_version_regex = start_version.replace(".", "\\.")
        if start_version == "":
            print("Looking for any previous image version")
            start_version_regex = "0\\.[0-3]\\.[0-9]{1,2}"
        docker_image_regex = re.compile(
            f"^([A-Za-z0-9_-]+/[A-Za-z0-9_-]+):v{start_version_regex}$"
        )

        def _new_docker_image(
            v,
        ):
            m = docker_image_regex.match(v)
            if m:
                return ":".join([m.groups()[0], f"v{finish_version}"])
            return None

        for k, v in config.get("default_images", {}).items():
            newimage = _new_docker_image(v)
            if newimage:
                print(f"In default_images: {k}: upgrading {v} to {newimage}")
                config["default_images"][k] = newimage

        for i, v in enumerate(config.get("profiles", {}).get("jupyterlab", [])):
            oldimage = v.get("kubespawner_override", {}).get("image", "")
            newimage = _new_docker_image(oldimage)
            if newimage:
                print(
                    f"In profiles: jupyterlab: [{i}]: upgrading {oldimage} to {newimage}"
                )
                config["profiles"]["jupyterlab"][i]["kubespawner_override"][
                    "image"
                ] = newimage

        for k, v in config.get("profiles", {}).get("dask_worker", {}).items():
            oldimage = v.get("image", "")
            newimage = _new_docker_image(oldimage)
            if newimage:
                print(
                    f"In profiles: dask_worker: {k}: upgrading {oldimage} to {newimage}"
                )
                config["profiles"]["dask_worker"][k]["image"] = newimage

        # Run any version-specific tasks
        return self._version_specific_upgrade(config, start_version)

    def _version_specific_upgrade(self, config, start_version):
        return config


class Upgrade_0_3_12(UpgradeStep):
    version = "0.3.12"

    def _version_specific_upgrade(self, config, start_version):
        """
        This verison of QHub requires a conda_store image for the first time.
        """
        if config.get("default_images", {}).get("conda_store", None) is None:
            newimage = f"quansight/qhub-conda-store:v{self.version}"
            print(f"Adding default_images: conda_store image as {newimage}")
            config["default_images"]["conda_store"] = newimage
        return config


# Manually-added upgrade steps must go above this line
if not UpgradeStep.has_step(__version__):
    # Always have a way to upgrade to the latest version number, even if no customizations
    class UpgradeLatest(UpgradeStep):
        version = __version__
