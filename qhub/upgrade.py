import logging
from ruamel import yaml
from abc import ABC
import pathlib

from packaging.version import parse as ver_parse

from pydantic.error_wrappers import ValidationError

from qhub.schema import verify

from .version import __version__

logger = logging.getLogger(__name__)

def do_upgrade(config_filename):

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    try:
        verify(config)
        logger.info(f"Your config file {config_filename} appears to be already up-to-date for qhub version {__version__}")
        return
    except (ValidationError, ValueError) as e:
        if config.get('qhub_version', '') == __version__:
            # There is an unrelated validation problem
            logging.info(f"Your config file {config_filename} appears to be already up-to-date for qhub version {__version__} but there is another validation error.\n")
            raise e

    logger.info("Doing upgrade")

    start_version = config.get('qhub_version', '')

    newconfig = UpgradeStep.upgrade(config, start_version, __version__)

    # Backup old file
    backup_filename = pathlib.Path(f'{config_filename}.{start_version}backup')

    if backup_filename.exists():
        raise ValueError(f"Cannot rename {config_filename} to {backup_filename} as destination file already exists. Aborting - please remove file and try again.")
    
    config_filename.rename(backup_filename)
    logging.info(f"Backing up old config in {backup_filename}")

    with config_filename.open("wt") as f:
        yaml.dump(config, f, default_flow_style=False, Dumper=yaml.RoundTripDumper)

    logging.info(f"Saving new config file {config_filename} ready for QHub version {__version__}")

class UpgradeStep(ABC):
    _steps = {}

    version = '' # Each subclass must have a version

    def __init_subclass__(cls):
        assert cls.version != ''
        assert cls.version not in cls._steps # Would mean multiple upgrades for the same step
        cls._steps[cls.version] = cls

    @classmethod
    def has_step(cls, version):
        return version in cls._steps

    @classmethod
    def upgrade(cls, config, start_version, finish_version):
        starting_ver = ver_parse(start_version)
        finish_ver = ver_parse(finish_version)
        step_versions = sorted([ver_parse(v) for v in cls._steps.keys() if ver_parse(v) > starting_ver and ver_parse(v) <= finish_ver])

        current_start_version = start_version
        for stepcls in [cls._steps[str(v)] for v in step_versions]:
            step = stepcls()
            config = step.upgrade_step(config, current_start_version)
            current_start_version = step.get_version()

        return config

    def get_version(self):
        return self.version
    
    def upgrade_step(self, config, start_version):

        logging.info(f"\nStarting upgrade from {start_version} to {self.get_version()}")

        # Set the new version
        if start_version != '':
            assert config.get('qhub_version', '') == start_version
        config['qhub_version'] = self.version

        return self._version_specific_upgrade(config, start_version)

    def _version_specific_upgrade(self, config, start_version):
        return config


class Upgrade_0_3_11(UpgradeStep):
    version = '0.3.11'


# Manually-added upgrade steps must go above this line
if not UpgradeStep.has_step(__version__):
    # Always have a way to upgrade to the latest version number, even if no customizations
    class UpgradeLatest(UpgradeStep):
        version = __version__
    