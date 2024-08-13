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


def create_navigator(navigator_type, params):
    """Create and return a navigator instance."""
    return navigator_factory(navigator_type, **params)


@pytest.fixture(scope="session")
def navigator_session(request, pytestconfig):
    session_type = request.param.get("session_type")
    extra_params = request.param.get("extra_params", {})

    params = build_params(request, pytestconfig, extra_params)

    nav = create_navigator(session_type, params)

    # Setup and teardown the navigator instance (could be improved)
    try:
        if session_type == "login":
            nav.login()
        elif session_type == "server":
            nav.start_server()
        yield nav
    except Exception as e:
        logger.debug(e)
        raise
    finally:
        try:
            if session_type == "login":
                nav.logout()
            elif session_type == "server":
                nav.stop_server()
        except Exception as e:
            logger.debug(e)
        nav.teardown()


def parameterized_fixture(session_type, **extra_params):
    """Utility function to create parameterized pytest fixtures."""
    return pytest.mark.parametrize(
        "navigator_session",
        [{"session_type": session_type, "extra_params": extra_params}],
        indirect=True,
    )


def server_parameterized(instance_name=None, **kwargs):
    return parameterized_fixture("server", instance_name=instance_name, **kwargs)


def login_parameterized(**kwargs):
    return parameterized_fixture("login", **kwargs)


@pytest.fixture(scope="function")
def navigator(navigator_session):
    """High-level navigator instance. Can be overridden based on the available
    parameterized decorator."""
    yield navigator_session


@pytest.fixture(scope="session")
def test_data_root():
    return Path(__file__).parent / "notebooks"
