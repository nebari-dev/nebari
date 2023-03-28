import os

import dotenv
import pytest
from basic import Navigator


@pytest.fixture(scope="session")
def _navigator_session(browser_name):
    """Set up a navigator instance, login with username/password, start
    a server. Teardown when session is complete. Use `navigator` fixture
    for individual tests."""
    dotenv.load_dotenv()
    nav = Navigator(
        nebari_url=os.environ["NEBARI_FULL_URL"],
        username=os.environ["USERNAME"],
        password=os.environ["PASSWORD"],
        headless=False,
        browser=browser_name,
        auth="password",
        instance_name=os.environ["INSTANCE_NAME"],
    )
    nav.login_password()
    nav.start_server()
    yield nav

    nav.teardown()


@pytest.fixture(scope="function")
def navigator(_navigator_session):
    """High level navigator instance with a reset workspace."""
    _navigator_session.reset_workspace()
    yield _navigator_session
