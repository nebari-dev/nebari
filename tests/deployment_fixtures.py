import logging
import pytest
import os
from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning

import yaml

from _nebari.deploy import deploy_configuration
from _nebari.destroy import destroy_configuration
from _nebari.render import render_template
from .utils import render_config_partial

import random
import string
import warnings

DEPLOYMENT_DIR = '_test_deploy'

logger = logging.getLogger(__name__)


def random_letters(length=5):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length)).lower()


def get_or_create_deployment_directory(cloud):
    # deployment_dirs = list(Path(Path(DEPLOYMENT_DIR) / cloud).glob("do*"))
    deployment_dirs = list(Path(Path(DEPLOYMENT_DIR) / cloud).glob("pytestdoxvzyr"))
    if deployment_dirs:
        deployment_dir = deployment_dirs[0]
    else:
        project_name = f"pytest{cloud}{random_letters()}"
        deployment_dir = Path(Path(Path(DEPLOYMENT_DIR) / cloud) / project_name)
        deployment_dir.mkdir()
    return deployment_dir


@pytest.fixture
def deploy(
        request,
):
    # Ignore this for now, as test is failing due to a
    # DeprecationWarning
    cloud = request.param
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
    deployment_dir = get_or_create_deployment_directory(cloud)
    config = render_config_partial(
        project_name=deployment_dir.name,
        namespace="dev",
        nebari_domain=f"{cloud}.nebari.dev",
        cloud_provider=cloud,
        ci_provider="github-actions",
        auth_provider="github",
    )
    deployment_dir_abs = deployment_dir.absolute()
    os.chdir(deployment_dir)
    print(f"Temporary directory: {deployment_dir}")
    with open(Path("nebari-config.yaml"), "w") as f:
        yaml.dump(config, f)
    render_template(deployment_dir_abs, Path("nebari-config.yaml"))
    try:
        deploy_configuration(
            config=config,
            dns_provider="cloudflare",
            dns_auto_provision=True,
            disable_prompt=True,
            disable_checks=False,
            skip_remote_state_provision=False,
        )
    except Exception as e:
        print(f"Deploy Failed, Exception: {e}")
        logger.exception(e)
        raise
    assert 1 == 1


def destroy(cloud):
    deployment_dirs = list(Path(Path(DEPLOYMENT_DIR) / cloud).glob(f"{cloud}*"))
    if not deployment_dirs:
        print("Configuration not found")
        destroy_configuration(deployment_dirs[0] / Path("nebari-config.yaml"))


def on_cloud(param):
    return pytest.mark.parametrize("deploy", [param], indirect=True)
