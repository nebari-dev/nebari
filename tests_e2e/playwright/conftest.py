import logging
import os
from pathlib import Path

import dotenv
import pytest
from navigator import Navigator

logger = logging.getLogger()


@pytest.fixture(scope="session")
def _navigator_session(browser_name, pytestconfig):
    """Set up a navigator instance, login with username/password, start
    a server. Teardown when session is complete.
    Do not use this for individual tests, use `navigator` fixture
    for tests."""
    dotenv.load_dotenv()
    # try/except added here in attempt to reach teardown after error in
    # order to close the browser context which will save the video so I debug
    # the error.
    try:
        nav = Navigator(
            nebari_url=os.environ["NEBARI_FULL_URL"],
            username=os.environ["KEYCLOAK_USERNAME"],
            password=os.environ["KEYCLOAK_PASSWORD"],
            headless=not pytestconfig.getoption("--headed"),
            slow_mo=pytestconfig.getoption("--slowmo"),
            browser=browser_name,
            auth="password",
            instance_name="small-instance",  # small-instance included by default
            video_dir="videos/",
        )
    except Exception as e:
        logger.debug(e)
        raise

    try:
        nav.login_password()
        nav.start_server()
        yield nav
    except Exception as e:
        logger.debug(e)
        raise
    finally:
        nav.teardown()


@pytest.fixture(scope="function")
def navigator(_navigator_session):
    """High level navigator instance with a reset workspace."""
    _navigator_session.reset_workspace()
    yield _navigator_session


@pytest.fixture(scope="session")
def test_data_root():
    here = Path(__file__).parent
    return here / "test_data"
