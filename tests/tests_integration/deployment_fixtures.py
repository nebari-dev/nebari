import logging
import os
import pprint
import random
import shutil
import string
import uuid
import warnings
from pathlib import Path

import pytest
from urllib3.exceptions import InsecureRequestWarning

from _nebari.config import read_configuration, write_configuration
from _nebari.deploy import deploy_configuration
from _nebari.destroy import destroy_configuration
from _nebari.provider.cloud.amazon_web_services import aws_cleanup
from _nebari.provider.cloud.azure_cloud import azure_cleanup
from _nebari.provider.cloud.digital_ocean import digital_ocean_cleanup
from _nebari.provider.cloud.google_cloud import gcp_cleanup
from _nebari.render import render_template
from _nebari.utils import set_do_environment
from nebari import schema
from tests.common.config_mod_utils import add_gpu_config, add_preemptible_node_group
from tests.tests_unit.utils import render_config_partial

DEPLOYMENT_DIR = "_test_deploy"
CONFIG_FILENAME = "nebari-config.yaml"
DOMAIN = "ci-{cloud}.nebari.dev"
DEFAULT_IMAGE_TAG = "main"

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


def _delete_deployment_directory(deployment_dir: Path):
    """Delete the deployment directory if it exists."""
    config = list(deployment_dir.glob(CONFIG_FILENAME))
    if len(config) == 1:
        logger.info(f"Deleting deployment directory: {deployment_dir}")
        shutil.rmtree(deployment_dir)


def _set_nebari_creds_in_environment(config):
    os.environ["NEBARI_FULL_URL"] = f"https://{config.domain}/"
    os.environ["KEYCLOAK_USERNAME"] = "pytest"
    os.environ["KEYCLOAK_PASSWORD"] = os.environ.get(
        "PYTEST_KEYCLOAK_PASSWORD", uuid.uuid4().hex
    )


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


def _cleanup_nebari(config: schema.Main):
    """Forcefully clean up any lingering resources."""

    cloud_provider = config.provider

    if cloud_provider == schema.ProviderEnum.do.value.lower():
        logger.info("Forcefully clean up Digital Ocean resources")
        digital_ocean_cleanup(config)
    elif cloud_provider == schema.ProviderEnum.aws.lower():
        logger.info("Forcefully clean up AWS resources")
        aws_cleanup(config)
    elif cloud_provider == schema.ProviderEnum.gcp.lower():
        logger.info("Forcefully clean up GCP resources")
        gcp_cleanup(config)
    elif cloud_provider == schema.ProviderEnum.azure.lower():
        logger.info("Forcefully clean up Azure resources")
        azure_cleanup(config)


@pytest.fixture(scope="session")
def deploy(request):
    """Deploy Nebari on the given cloud."""
    ignore_warnings()
    cloud = request.config.getoption("--cloud")

    # initialize
    if cloud == "do":
        set_do_environment()

    deployment_dir = _get_or_create_deployment_directory(cloud)
    config = render_config_partial(
        project_name=deployment_dir.name,
        namespace="dev",
        nebari_domain=DOMAIN.format(cloud=cloud),
        cloud_provider=cloud,
        ci_provider="github-actions",
        auth_provider="password",
    )

    deployment_dir_abs = deployment_dir.absolute()
    os.chdir(deployment_dir)
    logger.info(f"Temporary directory: {deployment_dir}")
    config_path = Path(CONFIG_FILENAME)

    write_configuration(config_path, config)

    from nebari.plugins import nebari_plugin_manager

    stages = nebari_plugin_manager.ordered_stages
    config_schema = nebari_plugin_manager.config_schema

    config = read_configuration(config_path, config_schema)

    # Modify config
    config.certificate.type = "lets-encrypt"
    config.certificate.acme_email = "internal-devops@quansight.com"
    config.certificate.acme_server = "https://acme-v02.api.letsencrypt.org/directory"
    config.dns.provider = "cloudflare"
    config.dns.auto_provision = True
    config.default_images.jupyterhub = (
        f"quay.io/nebari/nebari-jupyterhub:{DEFAULT_IMAGE_TAG}"
    )
    config.default_images.jupyterlab = (
        f"quay.io/nebari/nebari-jupyterlab:{DEFAULT_IMAGE_TAG}"
    )
    config.default_images.dask_worker = (
        f"quay.io/nebari/nebari-dask-worker:{DEFAULT_IMAGE_TAG}"
    )

    if cloud in ["aws"]:
        config = add_gpu_config(config, cloud=cloud)
        config = add_preemptible_node_group(config, cloud=cloud)

    print("*" * 100)
    pprint.pprint(config.model_dump())
    print("*" * 100)

    # render
    render_template(deployment_dir_abs, config, stages)

    failed = False

    # deploy
    try:
        logger.info("*" * 100)
        logger.info(f"Deploying Nebari on {cloud}")
        logger.info("*" * 100)
        stage_outputs = deploy_configuration(
            config=config,
            stages=stages,
            disable_prompt=True,
            disable_checks=False,
        )
        _create_nebari_user(config)
        _set_nebari_creds_in_environment(config)
        yield stage_outputs
    except Exception as e:
        failed = True
        logger.exception(e)
        logger.error(f"Deploy Failed, Exception: {e}")

    # destroy
    try:
        logger.info("*" * 100)
        logger.info("Tearing down")
        logger.info("*" * 100)
        destroy_configuration(config, stages)
    except Exception as e:
        logger.exception(e)
        logger.error("Destroy failed!")
        raise
    finally:
        logger.info("*" * 100)
        logger.info("Cleaning up any lingering resources")
        logger.info("*" * 100)
        try:
            _cleanup_nebari(config)
        except Exception as e:
            logger.exception(e)
            logger.error(
                "Cleanup failed, please check if there are any lingering resources!"
            )
        _delete_deployment_directory(deployment_dir_abs)

    if failed:
        raise AssertionError("Deployment failed")
