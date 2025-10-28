import warnings

# Suppress Python 3.10 EOL warning from google-api-core
warnings.filterwarnings(
    "ignore",
    message=r"You are using a Python version \(3\.10\..*\) which Google will stop supporting",
    category=FutureWarning,
    module="google.api_core",
)
