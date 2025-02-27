import logging
import os
import warnings
from pathlib import Path

import pytest
from urllib3.exceptions import InsecureRequestWarning

from _nebari.config import read_configuration

pytest_plugins = [
    "tests.common.playwright_fixtures",
]

CONFIG_FILENAME = "nebari-config.yaml"

logger = logging.getLogger(__name__)


def ignore_warnings():
    # Ignore this for now, as test is failing due to a
    # DeprecationWarning and InsecureRequestWarning
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)


@pytest.fixture(autouse=True)
def disable_warnings():
    ignore_warnings()


def _nebari_config(config_path):
    """Reads the Nebari configuration file from the specified path."""
    from nebari.plugins import nebari_plugin_manager

    config_schema = nebari_plugin_manager.config_schema
    return read_configuration(config_path, config_schema)


@pytest.fixture()
def nebari_config(deployment_dir):
    """Get the url of the nebari deployment from the nebari-config file"""
    config_path = deployment_dir / CONFIG_FILENAME
    return _nebari_config(config_path)


@pytest.fixture()
def nebari_endpoint(deployment_dir):
    """Get the url of the nebari deployment from the nebari-config file"""
    config_path = deployment_dir / CONFIG_FILENAME
    config = _nebari_config(config_path)
    return config.domain


@pytest.fixture(scope="session")
def deployment_dir(request) -> Path:
    """Ensures the deployment directory and config file exists
    and returns the path to it.
    """
    existing_deployment = Path(os.environ.get("EXISTING_DEPLOYMENT_DIR", ""))
    assert existing_deployment.exists()
    return existing_deployment.absolute()
