import logging
import os
from pathlib import Path

import dotenv
import pytest

from tests.common.navigator import navigator_factory

logger = logging.getLogger()


def load_env_vars():
    """Load environment variables using dotenv and return necessary parameters."""
    dotenv.load_dotenv()
    return {
        "nebari_url": os.getenv("NEBARI_FULL_URL"),
        "username": os.getenv("KEYCLOAK_USERNAME"),
        "password": os.getenv("KEYCLOAK_PASSWORD"),
    }


def build_params(request, pytestconfig, extra_params=None):
    """Construct and return parameters for navigator instances."""
    env_vars = load_env_vars()
    params = {
        "nebari_url": request.param.get("nebari_url") or env_vars["nebari_url"],
        "username": request.param.get("keycloak_username") or env_vars["username"],
        "password": request.param.get("keycloak_password") or env_vars["password"],
        "auth": "password",
        "headless": pytestconfig.getoption("--headless"),
        "slow_mo": pytestconfig.getoption("--slowmo"),
    }
    if extra_params:
        params.update(extra_params)
    return params


def create_navigator(navigator_type, request, pytestconfig, extra_params=None):
    """Create and return a navigator instance."""
    params = build_params(request, pytestconfig, extra_params)
    return navigator_factory(navigator_type, **params)


@pytest.fixture(scope="session")
def _login_session(request, pytestconfig):
    nav = create_navigator("login", request, pytestconfig)
    try:
        nav.login()
        yield nav
    except Exception as e:
        logger.debug(e)
        raise
    finally:
        try:
            nav.logout()
        except Exception as e:
            logger.debug(e)
        nav.teardown()


@pytest.fixture(scope="session")
def _server_session(request, pytestconfig):
    extra_params = {"instance_name": request.param.get("instance_name")}
    nav = create_navigator("server", request, pytestconfig, extra_params)
    try:
        nav.start_server()
        yield nav
    except Exception as e:
        logger.debug(e)
        raise
    finally:
        try:
            nav.stop_server()
        except Exception as e:
            logger.debug(e)
        nav.teardown()


@pytest.fixture(scope="function")
def navigator(_server_session):
    """High-level navigator instance with a reset workspace."""
    yield _server_session


def parameterized_fixture(fixture_name, **params):
    """Utility function to create parameterized pytest fixtures."""
    return pytest.mark.parametrize(fixture_name, [params], indirect=True)


def server_parameterized(
    nebari_url=None, keycloak_username=None, keycloak_password=None, instance_name=None
):
    return parameterized_fixture(
        "_server_session",
        nebari_url=nebari_url,
        keycloak_username=keycloak_username,
        keycloak_password=keycloak_password,
        instance_name=instance_name,
    )


def login_parameterized(
    nebari_url=None, keycloak_username=None, keycloak_password=None
):
    return parameterized_fixture(
        "_login_session",
        nebari_url=nebari_url,
        keycloak_username=keycloak_username,
        keycloak_password=keycloak_password,
    )


@pytest.fixture(scope="session")
def test_data_root():
    return Path(__file__).parent / "notebooks"
