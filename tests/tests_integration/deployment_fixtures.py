import logging
import os
import random
import string
import warnings
from pathlib import Path

import pytest
from urllib3.exceptions import InsecureRequestWarning

from _nebari.deploy import deploy_configuration
from _nebari.destroy import destroy_configuration
from _nebari.render import render_template
from _nebari.utils import yaml
from tests.common.gpu_config import add_gpu_config
from tests.tests_unit.utils import render_config_partial

DEPLOYMENT_DIR = "_test_deploy"

logger = logging.getLogger(__name__)


def ignore_warnings():
    # Ignore this for now, as test is failing due to a
    # DeprecationWarning and InsecureRequestWarning
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)


@pytest.fixture(autouse=True)
def disable_warnings():
    ignore_warnings()


def _random_letters(length=5):
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(length)).lower()


def _get_or_create_deployment_directory(cloud):
    """This will create a directory to initialise and deploy
    Nebari from.
    """
    deployment_dirs = list(Path(Path(DEPLOYMENT_DIR) / cloud).glob(f"pytest{cloud}*"))
    if deployment_dirs:
        deployment_dir = deployment_dirs[0]
    else:
        project_name = f"pytest{cloud}{_random_letters()}"
        deployment_dir = Path(Path(Path(DEPLOYMENT_DIR) / cloud) / project_name)
        deployment_dir.mkdir(parents=True)
    return deployment_dir


def _set_do_environment():
    os.environ["AWS_ACCESS_KEY_ID"] = os.environ["SPACES_ACCESS_KEY_ID"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ["SPACES_SECRET_ACCESS_KEY"]


def _set_nebari_creds_in_environment(config):
    os.environ["NEBARI_FULL_URL"] = f"https://{config['domain']}/"
    os.environ["KEYCLOAK_USERNAME"] = 'pytest'
    os.environ["KEYCLOAK_PASSWORD"] = 'pytest-password'


def _create_nebari_user(config):
    import keycloak
    from _nebari.keycloak import create_user, get_keycloak_admin_from_config
    keycloak_admin = get_keycloak_admin_from_config(config)
    try:
        user = create_user(keycloak_admin, "pytest", "pytest-password")
        return user
    except keycloak.KeycloakPostError as e:
        if e.response_code == 409:
            logger.info(f"User already exists: {e.response_body}")


@pytest.fixture(scope="session")
def deploy(request):
    """Deploy Nebari on the given cloud, currently only DigitalOcean"""
    ignore_warnings()
    cloud = request.param
    logger.info(f"Deploying: {cloud}")
    if cloud == "do":
        _set_do_environment()
    deployment_dir = _get_or_create_deployment_directory(cloud)
    config = render_config_partial(
        project_name=deployment_dir.name,
        namespace="dev",
        nebari_domain=f"ci-{cloud}.nebari.dev",
        cloud_provider=cloud,
        ci_provider="github-actions",
        auth_provider="github",
    )
    # Generate certificate as well
    config['certificate'] = {
        "type": "lets-encrypt",
        "acme_email": "internal-devops@quansight.com",
        "acme_server": "https://acme-v02.api.letsencrypt.org/directory",
    }
    if cloud == "aws":
        config = add_gpu_config(config)
    deployment_dir_abs = deployment_dir.absolute()
    os.chdir(deployment_dir)
    logger.info(f"Temporary directory: {deployment_dir}")
    config_path = Path("nebari-config.yaml")
    if not config_path.exists():
        with open(config_path, "w") as f:
            yaml.dump(config, f)
    else:
        # We don't want to overwrite keycloak config for development
        with open(config_path) as f:
            current_config = yaml.load(f)
            config['security']['keycloak']['initial_root_password'] = current_config['security']['keycloak']['initial_root_password']

    render_template(deployment_dir_abs, Path("nebari-config.yaml"))
    try:
        deploy_config = deploy_configuration(
            config=config,
            dns_provider="cloudflare",
            dns_auto_provision=True,
            disable_prompt=True,
            disable_checks=False,
            skip_remote_state_provision=False,
        )
        _create_nebari_user(config)
        _set_nebari_creds_in_environment(config)
        yield deploy_config
    except Exception as e:
        logger.info(f"Deploy Failed, Exception: {e}")
        logger.exception(e)
    logger.info("Tearing down")
    return _destroy(config)


def _destroy(config):
    destroy_configuration(config)


def on_cloud(param=None):
    all_clouds = ["aws", "do"]

    def _create_pytest_param(cloud):
        return pytest.param(cloud, marks=getattr(pytest.mark, cloud))

    all_clouds_param = map(_create_pytest_param, all_clouds)
    params = [_create_pytest_param(param)] if param else all_clouds_param
    return pytest.mark.parametrize("deploy", params, indirect=True)
