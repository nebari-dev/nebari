import pytest

pytest_plugins = [
    "tests.tests_integration.deployment_fixtures",
    "tests.common.playwright_fixtures",
]


# argparse under-the-hood
def pytest_addoption(parser):
    parser.addoption(
        "--cloud", action="store", help="Cloud to deploy on: aws/do/gcp/azure"
    )


@pytest.fixture
def local_test_credential():
    import os

    username = os.environ.get("EXAMPLE_USER_NAME", None)
    password = os.environ.get("EXAMPLE_USER_PASSWORD", None)
    domain = os.environ.get("TEST_DOMAIN", None)
    assert None not in [
        username,
        password,
        domain,
    ], f"Missing required environment variables:\nEXAMPLE_USER_NAME: {username}, EXAMPLE_USER_PASSWORD: {password}, TEST_DOMAIN: {domain}"
    return username, password, domain
