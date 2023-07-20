import logging
import pytest
import os
import warnings

from pathlib import Path

import yaml

from _nebari.deploy import deploy_configuration
from _nebari.destroy import destroy_configuration
from _nebari.render import render_template
from urllib3.exceptions import InsecureRequestWarning
from tests.utils import render_config_partial

import random
import string

DEPLOYMENT_DIR = '_test_deploy'

logger = logging.getLogger(__name__)


def ignore_warnings():
    # Ignore this for now, as test is failing due to a
    # DeprecationWarning and InsecureRequestWarning
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)


def random_letters(length=5):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length)).lower()


def get_or_create_deployment_directory(cloud):
    deployment_dirs = list(Path(Path(DEPLOYMENT_DIR) / cloud).glob(f"pytest{cloud}*"))
    if deployment_dirs:
        deployment_dir = deployment_dirs[0]
    else:
        project_name = f"pytest{cloud}{random_letters()}"
        deployment_dir = Path(Path(Path(DEPLOYMENT_DIR) / cloud) / project_name)
        deployment_dir.mkdir(parents=True)
    return deployment_dir


def set_do_environment():
    os.environ['AWS_ACCESS_KEY_ID'] = os.environ['SPACES_ACCESS_KEY_ID']
    os.environ['AWS_SECRET_ACCESS_KEY'] = os.environ['SPACES_SECRET_ACCESS_KEY']


@pytest.fixture(scope="session")
def deploy(request):
    ignore_warnings()
    cloud = request.param
    set_do_environment()
    deployment_dir = get_or_create_deployment_directory(cloud)
    config = render_config_partial(
        project_name=deployment_dir.name,
        namespace="dev",
        nebari_domain=f"ci-{cloud}.nebari.dev",
        cloud_provider=cloud,
        ci_provider="github-actions",
        auth_provider="github",
    )
    deployment_dir_abs = deployment_dir.absolute()
    os.chdir(deployment_dir)
    logger.info(f"Temporary directory: {deployment_dir}")
    with open(Path("nebari-config.yaml"), "w") as f:
        yaml.dump(config, f)
    render_template(deployment_dir_abs, Path("nebari-config.yaml"))
    try:
        yield deploy_configuration(
            config=config,
            dns_provider="cloudflare",
            dns_auto_provision=True,
            disable_prompt=True,
            disable_checks=False,
            skip_remote_state_provision=False,
        )
    except Exception as e:
        logger.info(f"Deploy Failed, Exception: {e}")
        logger.exception(e)
        raise
    logger.info("Teardown")
    return destroy(config)


def destroy(config):
    destroy_configuration(config)


def on_cloud(param):
    return pytest.mark.parametrize("deploy", [param], indirect=True)
