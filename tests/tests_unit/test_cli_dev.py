import json
import tempfile
from pathlib import Path
from typing import Any, List
from unittest.mock import Mock, patch

import pytest
import requests.exceptions
import yaml
from typer.testing import CliRunner

from _nebari.cli import create_cli

TEST_KEYCLOAKAPI_REQUEST = "GET /"  # get list of realms

TEST_DOMAIN = "nebari.example.com"
MOCK_KEYCLOAK_ENV = {
    "KEYCLOAK_SERVER_URL": f"https://{TEST_DOMAIN}/auth/",
    "KEYCLOAK_ADMIN_USERNAME": "root",
    "KEYCLOAK_ADMIN_PASSWORD": "super-secret-123!",
}

TEST_ACCESS_TOKEN = "abc123"

TEST_REALMS = [
    {"id": "test-realm", "realm": "test-realm"},
    {"id": "master", "realm": "master"},
]

runner = CliRunner()


@pytest.mark.parametrize(
    "args, exit_code, content",
    [
        # --help
        ([], 0, ["Usage:"]),
        (["--help"], 0, ["Usage:"]),
        (["-h"], 0, ["Usage:"]),
        (["keycloak-api", "--help"], 0, ["Usage:"]),
        (["keycloak-api", "-h"], 0, ["Usage:"]),
        # error, missing args
        (["keycloak-api"], 2, ["Missing option"]),
        (["keycloak-api", "--config"], 2, ["requires an argument"]),
        (["keycloak-api", "-c"], 2, ["requires an argument"]),
        (["keycloak-api", "--request"], 2, ["requires an argument"]),
        (["keycloak-api", "-r"], 2, ["requires an argument"]),
    ],
)
def test_cli_dev_stdout(args: List[str], exit_code: int, content: List[str]):
    app = create_cli()
    result = runner.invoke(app, ["dev"] + args)
    assert result.exit_code == exit_code
    for c in content:
        assert c in result.stdout


def mock_api_post(admin_password: str, url: str, headers: Any, data: Any, verify: bool):
    response = Mock()
    if (
        url
        == f"{MOCK_KEYCLOAK_ENV['KEYCLOAK_SERVER_URL']}realms/master/protocol/openid-connect/token"
        and data["password"] == admin_password
    ):
        response.status_code = 200
        response.content = bytes(
            json.dumps({"access_token": TEST_ACCESS_TOKEN}), "UTF-8"
        )
    else:
        response.status_code = 403
    return response


def mock_api_request(
    access_token: str, method: str, url: str, headers: Any, verify: bool
):
    response = Mock()
    if (
        method == "GET"
        and url == f"{MOCK_KEYCLOAK_ENV['KEYCLOAK_SERVER_URL']}admin/realms/"
        and headers["Authorization"] == f"Bearer {access_token}"
    ):
        response.status_code = 200
        response.content = bytes(json.dumps(TEST_REALMS), "UTF-8")
    else:
        response.status_code = 403
    return response


@patch(
    "_nebari.keycloak.requests.post",
    side_effect=lambda url, headers, data, verify: mock_api_post(
        MOCK_KEYCLOAK_ENV["KEYCLOAK_ADMIN_PASSWORD"], url, headers, data, verify
    ),
)
@patch(
    "_nebari.keycloak.requests.request",
    side_effect=lambda method, url, headers, verify: mock_api_request(
        TEST_ACCESS_TOKEN, method, url, headers, verify
    ),
)
def test_cli_dev_keycloakapi_happy_path_from_env(
    _mock_requests_post, _mock_requests_request
):
    result = run_cli_dev(use_env=True)

    assert 0 == result.exit_code
    assert not result.exception

    r = json.loads(result.stdout)
    assert 2 == len(r)
    assert "test-realm" == r[0]["realm"]


@patch(
    "_nebari.keycloak.requests.post",
    side_effect=lambda url, headers, data, verify: mock_api_post(
        MOCK_KEYCLOAK_ENV["KEYCLOAK_ADMIN_PASSWORD"], url, headers, data, verify
    ),
)
@patch(
    "_nebari.keycloak.requests.request",
    side_effect=lambda method, url, headers, verify: mock_api_request(
        TEST_ACCESS_TOKEN, method, url, headers, verify
    ),
)
def test_cli_dev_keycloakapi_happy_path_from_config(
    _mock_requests_post, _mock_requests_request
):
    result = run_cli_dev(use_env=False)

    assert 0 == result.exit_code
    assert not result.exception

    r = json.loads(result.stdout)
    assert 2 == len(r)
    assert "test-realm" == r[0]["realm"]


@patch(
    "_nebari.keycloak.requests.post",
    side_effect=lambda url, headers, data, verify: mock_api_post(
        MOCK_KEYCLOAK_ENV["KEYCLOAK_ADMIN_PASSWORD"], url, headers, data, verify
    ),
)
def test_cli_dev_keycloakapi_error_bad_request(_mock_requests_post):
    result = run_cli_dev(request="malformed")

    assert 1 == result.exit_code
    assert result.exception
    assert "not enough values to unpack" in str(result.exception)


@patch(
    "_nebari.keycloak.requests.post",
    side_effect=lambda url, headers, data, verify: mock_api_post(
        "invalid_admin_password", url, headers, data, verify
    ),
)
def test_cli_dev_keycloakapi_error_authentication(_mock_requests_post):
    result = run_cli_dev()

    assert 1 == result.exit_code
    assert result.exception
    assert "Unable to retrieve Keycloak API token" in str(result.exception)
    assert "Status code: 403" in str(result.exception)


@patch(
    "_nebari.keycloak.requests.post",
    side_effect=lambda url, headers, data, verify: mock_api_post(
        MOCK_KEYCLOAK_ENV["KEYCLOAK_ADMIN_PASSWORD"], url, headers, data, verify
    ),
)
@patch(
    "_nebari.keycloak.requests.request",
    side_effect=lambda method, url, headers, verify: mock_api_request(
        "invalid_access_token", method, url, headers, verify
    ),
)
def test_cli_dev_keycloakapi_error_authorization(
    _mock_requests_post, _mock_requests_request
):
    result = run_cli_dev()

    assert 1 == result.exit_code
    assert result.exception
    assert "Unable to communicate with Keycloak API" in str(result.exception)
    assert "Status code: 403" in str(result.exception)


@patch(
    "_nebari.keycloak.requests.post", side_effect=requests.exceptions.RequestException()
)
def test_cli_dev_keycloakapi_request_exception(_mock_requests_post):
    result = run_cli_dev()

    assert 1 == result.exit_code
    assert result.exception


@patch("_nebari.keycloak.requests.post", side_effect=Exception())
def test_cli_dev_keycloakapi_unhandled_error(_mock_requests_post):
    result = run_cli_dev()

    assert 1 == result.exit_code
    assert result.exception


def run_cli_dev(
    request: str = TEST_KEYCLOAKAPI_REQUEST,
    use_env: bool = True,
    extra_args: List[str] = [],
):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        extra_config = (
            {
                "domain": TEST_DOMAIN,
                "security": {
                    "keycloak": {
                        "initial_root_password": MOCK_KEYCLOAK_ENV[
                            "KEYCLOAK_ADMIN_PASSWORD"
                        ]
                    }
                },
            }
            if not use_env
            else {}
        )
        config = {**{"project_name": "dev"}, **extra_config}
        with open(tmp_file.resolve(), "w") as f:
            yaml.dump(config, f)

        assert tmp_file.exists() is True

        app = create_cli()

        args = [
            "dev",
            "keycloak-api",
            "--config",
            tmp_file.resolve(),
            "--request",
            request,
        ] + extra_args

        env = MOCK_KEYCLOAK_ENV if use_env else {}
        result = runner.invoke(app, args=args, env=env)

        return result
