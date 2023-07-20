import logging
import os
import pathlib
from urllib3.exceptions import InsecureRequestWarning

import yaml

from _nebari.deploy import deploy_configuration
from _nebari.render import render_template
from .conftest import render_config_partial

import random
import string
import warnings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)9s %(lineno)4s %(module)s: %(message)s"
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def random_letters(length=5):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length)).lower()


def test_integration():
    # Ignore this for now, as test is failing due to a
    # DeprecationWarning
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
    # project_name = f"pytestdo{random_letters()}"
    project_name = "pytestdoxvzyr"
    config = render_config_partial(
        project_name=project_name,
        namespace="dev",
        nebari_domain="do.nebari.dev",
        cloud_provider="do",
        ci_provider="github-actions",
        auth_provider="github",
    )
    tmpdir = os.getcwd() / pathlib.Path("pytestdotemp")
    os.chdir(tmpdir)
    print(f"Temporary directory: {tmpdir}")
    config_filepath = tmpdir / "nebari-config.yaml"
    with open(config_filepath, "w") as f:
        yaml.dump(config, f)

    render_template(tmpdir, config_filepath)
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
