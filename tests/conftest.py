import warnings

warnings.filterwarnings(
    "ignore",
    message=r"You are using a Python version \(3\.10\..*\) which Google will stop supporting",
    category=FutureWarning,
    module="google.api_core",
)

pytest_plugins = ["tests.common.playwright_fixtures"]
