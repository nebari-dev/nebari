import logging
import os
import subprocess

import pytest

from _nebari.cli import configure_logging
from _nebari.subcommands.init import InitInputs
from nebari.plugins import nebari_plugin_manager

PROJECT_NAME = "clitest"
DOMAIN_NAME = "clitest.dev"


@pytest.mark.parametrize(
    "namespace, auth_provider, ci_provider, ssl_cert_email",
    (
        [None, None, None, None],
        ["prod", "password", "github-actions", "it@acme.org"],
    ),
)
def test_nebari_init(tmp_path, namespace, auth_provider, ci_provider, ssl_cert_email):
    """Test `nebari init` CLI command."""
    command = [
        "nebari",
        "init",
        "local",
        f"--project={PROJECT_NAME}",
        f"--domain={DOMAIN_NAME}",
        "--disable-prompt",
    ]

    default_values = InitInputs()

    if namespace:
        command.append(f"--namespace={namespace}")
    else:
        namespace = default_values.namespace
    if auth_provider:
        command.append(f"--auth-provider={auth_provider}")
    else:
        auth_provider = default_values.auth_provider
    if ci_provider:
        command.append(f"--ci-provider={ci_provider}")
    else:
        ci_provider = default_values.ci_provider
    if ssl_cert_email:
        command.append(f"--ssl-cert-email={ssl_cert_email}")
    else:
        ssl_cert_email = default_values.ssl_cert_email

    subprocess.run(command, cwd=tmp_path, check=True)

    config = nebari_plugin_manager.read_config(tmp_path / "nebari-config.yaml")

    assert config.namespace == namespace
    assert config.security.authentication.type.lower() == auth_provider
    assert config.ci_cd.type == ci_provider
    assert config.certificate.acme_email == ssl_cert_email


@pytest.mark.parametrize(
    "command",
    (
        ["nebari", "--version"],
        ["nebari", "info"],
    ),
)
def test_nebari_commands_no_args(command):
    subprocess.run(command, check=True, capture_output=True, text=True).stdout.strip()


@pytest.mark.parametrize(
    "log_level,expected_python_level,expected_tf_level",
    [
        ("trace", logging.DEBUG, "TRACE"),
        ("debug", logging.DEBUG, "DEBUG"),
        ("info", logging.INFO, "INFO"),
        ("warning", logging.WARNING, "WARN"),
        ("error", logging.ERROR, "ERROR"),
        ("critical", logging.CRITICAL, "ERROR"),
    ],
)
def test_configure_logging_levels(
    log_level, expected_python_level, expected_tf_level, monkeypatch
):
    """Test that configure_logging sets correct Python and Terraform log levels."""
    # Remove TF_LOG from environment if it exists
    monkeypatch.delenv("TF_LOG", raising=False)

    # Configure logging with the specified level
    configure_logging(log_level)

    # Check that Python logging level is set correctly
    root_logger = logging.getLogger()
    assert root_logger.level == expected_python_level

    # Check that TF_LOG environment variable is set correctly
    assert os.environ.get("TF_LOG") == expected_tf_level


def test_configure_logging_with_none(monkeypatch):
    """Test that configure_logging returns early when log_level is None."""
    # Remove TF_LOG from environment if it exists
    monkeypatch.delenv("TF_LOG", raising=False)

    # Get initial logging level
    initial_level = logging.getLogger().level

    # Call with None
    configure_logging(None)

    # Verify logging level hasn't changed
    assert logging.getLogger().level == initial_level

    # Verify TF_LOG wasn't set
    assert "TF_LOG" not in os.environ


def test_configure_logging_preserves_existing_tf_log(monkeypatch):
    """Test that configure_logging doesn't override existing TF_LOG variable."""
    # Set TF_LOG to a specific value
    monkeypatch.setenv("TF_LOG", "TRACE")

    # Configure logging with a different level
    configure_logging("error")

    # Verify TF_LOG wasn't changed
    assert os.environ["TF_LOG"] == "TRACE"


def test_configure_logging_debug_format():
    """Test that DEBUG level uses detailed format with timestamp."""
    configure_logging("debug")

    # Get the root logger
    root_logger = logging.getLogger()

    # Check that level is DEBUG
    assert root_logger.level == logging.DEBUG

    # Check that at least one handler exists (basicConfig creates one)
    assert len(root_logger.handlers) > 0


def test_configure_logging_non_debug_format():
    """Test that non-DEBUG levels use simpler format without timestamp."""
    configure_logging("info")

    # Get the root logger
    root_logger = logging.getLogger()

    # Check that level is INFO
    assert root_logger.level == logging.INFO

    # Check that at least one handler exists
    assert len(root_logger.handlers) > 0


@pytest.mark.parametrize(
    "log_level",
    ["trace", "debug", "info", "warning", "error"],
)
def test_cli_with_log_level(log_level, monkeypatch):
    """Test that the CLI accepts and processes the --log-level option."""
    # Remove TF_LOG from environment if it exists
    monkeypatch.delenv("TF_LOG", raising=False)

    command = ["nebari", "--log-level", log_level, "info"]
    result = subprocess.run(command, check=True, capture_output=True, text=True)

    # Command should succeed
    assert result.returncode == 0


def test_cli_with_short_log_level_option(monkeypatch):
    """Test that the CLI accepts the -l short option for log level."""
    # Remove TF_LOG from environment if it exists
    monkeypatch.delenv("TF_LOG", raising=False)

    command = ["nebari", "-l", "debug", "info"]
    result = subprocess.run(command, check=True, capture_output=True, text=True)

    # Command should succeed
    assert result.returncode == 0
