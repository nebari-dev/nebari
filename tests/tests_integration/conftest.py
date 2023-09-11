pytest_plugins = [
    "tests.tests_integration.deployment_fixtures",
    "tests.common.playwright_fixtures",
]


# argparse under-the-hood
def pytest_addoption(parser):
    parser.addoption(
        "--cloud", action="store", help="Cloud to deploy on: aws/do/gcp/azure"
    )
    parser.addoption(
        "--disable-prompt",
        action="store_true",
        help="Disable prompt for confirmation to start cluster teardown",
        default=False,
    )
