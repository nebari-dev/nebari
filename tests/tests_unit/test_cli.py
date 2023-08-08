import subprocess

import pytest

from _nebari.schema import InitInputs
from _nebari.utils import load_yaml

PROJECT_NAME = "clitest"
DOMAIN_NAME = "clitest.dev"


@pytest.mark.parametrize(
    "namespace, auth_provider, ci_provider, ssl_cert_email",
    (
        [None, None, None, None],
        ["prod", "github", "github-actions", "it@acme.org"],
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

    config = load_yaml(tmp_path / "nebari-config.yaml")

    assert config.get("namespace") == namespace
    assert (
        config.get("security", {}).get("authentication", {}).get("type").lower()
        == auth_provider
    )
    ci_cd = config.get("ci_cd", None)
    if ci_cd:
        assert ci_cd.get("type", {}) == ci_provider
    else:
        assert ci_cd == ci_provider
    acme_email = config.get("certificate", None)
    if acme_email:
        assert acme_email.get("acme_email") == ssl_cert_email
    else:
        assert acme_email == ssl_cert_email


def test_python_invocation():
    def run(command):
        return subprocess.run(
            command, check=True, capture_output=True, text=True
        ).stdout.strip()

    command = ["nebari", "--version"]

    actual = run(["python", "-m", *command])
    expected = run(command)

    assert actual == expected
