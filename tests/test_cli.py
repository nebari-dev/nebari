import os
import subprocess
import typing
from pathlib import Path

import pytest

from nebari.schema import InitInputs
from nebari.utils import load_yaml

PROJECT_NAME = "clitest"
DOMAIN_NAME = "clitest.dev"


def run_cli_cmd(command: str, working_dir: typing.Union[str, Path]):
    """Run the provided CLI command using subprocess."""

    try:
        os.chdir(working_dir)
        subprocess.call(command.split())
    except subprocess.CalledProcessError:
        return False

    return True


@pytest.mark.parametrize(
    "namespace, auth_provider, ci_provider, ssl_cert_email",
    (
        [None, None, None, None],
        ["prod", "github", "github-actions", "it@acme.org"],
    ),
)
def test_nebari_init(tmp_path, namespace, auth_provider, ci_provider, ssl_cert_email):
    """Test `nebari init` CLI command."""

    command = f"nebari init local --project {PROJECT_NAME} --domain {DOMAIN_NAME} --disable-prompt"

    default_values = InitInputs()

    if namespace:
        command += f" --namespace {namespace}"
    else:
        namespace = default_values.namespace
    if auth_provider:
        command += f" --auth-provider {auth_provider}"
    else:
        auth_provider = default_values.auth_provider
    if ci_provider:
        command += f" --ci-provider {ci_provider}"
    else:
        ci_provider = default_values.ci_provider
    if ssl_cert_email:
        command += f" --ssl-cert-email {ssl_cert_email}"
    else:
        ssl_cert_email = default_values.ssl_cert_email

    assert run_cli_cmd(command, tmp_path)

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
        ci_cd = config.get("ci_cd", None)
    acme_email = config.get("certificate", None)
    if acme_email:
        assert acme_email.get("acme_email") == ssl_cert_email
    else:
        assert acme_email == ssl_cert_email
