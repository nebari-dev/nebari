import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests.auth
import requests.exceptions
from typer.testing import CliRunner

from _nebari.cli import create_cli
from _nebari.provider.cicd.github import GITHUB_BASE_URL

runner = CliRunner()

TEST_GITHUB_USERNAME = "test-nebari-github-user"
TEST_GITHUB_TOKEN = "nebari-super-secret"

TEST_REPOSITORY_NAME = "nebari-test"

DEFAULT_ARGS = [
    "init",
    "local",
    "--project-name",
    "test",
    "--repository-auto-provision",
    "--repository",
    f"https://github.com/{TEST_GITHUB_USERNAME}/{TEST_REPOSITORY_NAME}",
]


@patch(
    "_nebari.provider.cicd.github.requests.get",
    side_effect=lambda url, json, auth: mock_api_request(
        "GET",
        url,
        json,
        auth,
    ),
)
@patch(
    "_nebari.provider.cicd.github.requests.post",
    side_effect=lambda url, json, auth: mock_api_request(
        "POST",
        url,
        json,
        auth,
    ),
)
@patch(
    "_nebari.provider.cicd.github.requests.put",
    side_effect=lambda url, json, auth: mock_api_request(
        "PUT",
        url,
        json,
        auth,
    ),
)
@patch(
    "_nebari.initialize.git",
    return_value=Mock(
        is_git_repo=Mock(return_value=False),
        initialize_git=Mock(return_value=True),
        add_git_remote=Mock(return_value=True),
    ),
)
def test_cli_init_repository_auto_provision(
    _mock_requests_get,
    _mock_requests_post,
    _mock_requests_put,
    _mock_git,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("GITHUB_USERNAME", TEST_GITHUB_USERNAME)
    monkeypatch.setenv("GITHUB_TOKEN", TEST_GITHUB_TOKEN)

    app = create_cli()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        result = runner.invoke(app, DEFAULT_ARGS + ["--output", tmp_file.resolve()])

        assert 0 == result.exit_code
        assert not result.exception
        assert tmp_file.exists() is True


@patch(
    "_nebari.provider.cicd.github.requests.get",
    side_effect=lambda url, json, auth: mock_api_request(
        "GET", url, json, auth, repo_exists=True
    ),
)
@patch(
    "_nebari.provider.cicd.github.requests.post",
    side_effect=lambda url, json, auth: mock_api_request(
        "POST",
        url,
        json,
        auth,
    ),
)
@patch(
    "_nebari.provider.cicd.github.requests.put",
    side_effect=lambda url, json, auth: mock_api_request(
        "PUT",
        url,
        json,
        auth,
    ),
)
@patch(
    "_nebari.initialize.git",
    return_value=Mock(
        is_git_repo=Mock(return_value=False),
        initialize_git=Mock(return_value=True),
        add_git_remote=Mock(return_value=True),
    ),
)
def test_cli_init_repository_repo_exists(
    _mock_requests_get,
    _mock_requests_post,
    _mock_requests_put,
    _mock_git,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
    caplog,
):
    monkeypatch.setenv("GITHUB_USERNAME", TEST_GITHUB_USERNAME)
    monkeypatch.setenv("GITHUB_TOKEN", TEST_GITHUB_TOKEN)

    with capsys.disabled():
        caplog.set_level(logging.WARNING)

        app = create_cli()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
            assert tmp_file.exists() is False

            result = runner.invoke(app, DEFAULT_ARGS + ["--output", tmp_file.resolve()])

            assert 0 == result.exit_code
            assert not result.exception
            assert tmp_file.exists() is True
            assert "already exists" in caplog.text


def test_cli_init_error_repository_missing_env(monkeypatch: pytest.MonkeyPatch):
    for e in [
        "GITHUB_USERNAME",
        "GITHUB_TOKEN",
    ]:
        try:
            monkeypatch.delenv(e)
        except Exception as e:
            pass

    app = create_cli()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        result = runner.invoke(app, DEFAULT_ARGS + ["--output", tmp_file.resolve()])

        assert 1 == result.exit_code
        assert result.exception
        assert "Environment variable(s) required for GitHub automation" in str(
            result.exception
        )
        assert tmp_file.exists() is False


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com",
        "http://github.com/user/repo",
        "https://github.com/user/" "github.com/user/repo",
        "https://notgithub.com/user/repository",
    ],
)
def test_cli_init_error_invalid_repo(url):
    app = create_cli()

    args = ["init", "local", "--project-name", "test", "--repository", url]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        result = runner.invoke(app, args + ["--output", tmp_file.resolve()])

        assert 2 == result.exit_code
        assert result.exception
        assert "repository URL" in str(result.stdout)
        assert tmp_file.exists() is False


def mock_api_request(
    method: str,
    url: str,
    json: str,
    auth: requests.auth.HTTPBasicAuth,
    repo_exists: bool = False,
):
    response = Mock()
    response.json = Mock(return_value={})
    response.raise_for_status = Mock(return_value=True)
    if (
        url.startswith(GITHUB_BASE_URL)
        and auth.username == TEST_GITHUB_USERNAME
        and auth.password == TEST_GITHUB_TOKEN
    ):
        response.status_code = 200
        if (
            not repo_exists
            and method == "GET"
            and url.endswith(f"repos/{TEST_GITHUB_USERNAME}/{TEST_REPOSITORY_NAME}")
        ):
            response.status_code = 404
            response.raise_for_status.side_effect = requests.exceptions.HTTPError
        elif method == "GET" and url.endswith(
            f"repos/{TEST_GITHUB_USERNAME}/{TEST_REPOSITORY_NAME}/actions/secrets/public-key"
        ):
            response.json = Mock(
                return_value={
                    "key": "hBT5WZEj8ZoOv6TYJsfWq7MxTEQopZO5/IT3ZCVQPzs=",
                    "key_id": "012345678912345678",
                }
            )
    else:
        response.status_code = 403
        response.raise_for_status.side_effect = requests.exceptions.HTTPError
    return response
