import subprocess

import pytest

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
