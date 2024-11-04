import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml
from typer.testing import CliRunner

from _nebari._version import __version__
from _nebari.cli import create_cli

TEST_DATA_DIR = Path(__file__).resolve().parent / "cli_validate"

runner = CliRunner()


def _update_yaml_file(file_path: Path, key: str, value: Any):
    """Utility function to update a yaml file with a new key/value pair."""
    with open(file_path, "r") as f:
        yaml_data = yaml.safe_load(f)

    yaml_data[key] = value

    with open(file_path, "w") as f:
        yaml.safe_dump(yaml_data, f)


@pytest.mark.parametrize(
    "args, exit_code, content",
    [
        # --help
        (["--help"], 0, ["Usage:"]),
        (["-h"], 0, ["Usage:"]),
        # error, missing args
        ([], 2, ["Missing option"]),
        (["--config"], 2, ["requires an argument"]),
        (["-c"], 2, ["requires an argument"]),
        (
            ["--enable-commenting"],
            2,
            ["Missing option"],
        ),  # https://github.com/nebari-dev/nebari/issues/1937
    ],
)
def test_cli_validate_stdout(args: List[str], exit_code: int, content: List[str]):
    app = create_cli()
    result = runner.invoke(app, ["validate"] + args)
    assert result.exit_code == exit_code
    for c in content:
        assert c in result.stdout


def generate_test_data_test_cli_validate_local_happy_path():
    """
    Search the cli_validate folder for happy path test cases
    and add them to the parameterized list of inputs for
    test_cli_validate_local_happy_path
    """

    test_data = []
    for f in TEST_DATA_DIR.iterdir():
        if f.is_file() and re.match(
            r"^\w*\.happy.*\.yaml$", f.name
        ):  # sample.happy.optional-description.yaml
            test_data.append((f.name))
    keys = [
        "config_yaml",
    ]
    return {"keys": keys, "test_data": test_data}


def test_cli_validate_local_happy_path(config_yaml: str):
    test_file = TEST_DATA_DIR / config_yaml
    assert test_file.exists() is True

    with tempfile.TemporaryDirectory() as tmpdirname:
        temp_test_file = shutil.copy(test_file, tmpdirname)

        # update the copied test file with the current version if necessary
        _update_yaml_file(temp_test_file, "nebari_version", __version__)

        app = create_cli()
        result = runner.invoke(app, ["validate", "--config", temp_test_file])
        assert not result.exception
        assert 0 == result.exit_code
        assert "Successfully validated configuration" in result.stdout


def test_cli_validate_from_env():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        nebari_config = yaml.safe_load(
            """
provider: aws
project_name: test
amazon_web_services:
  region: us-east-1
  kubernetes_version: '1.19'
        """
        )

        with open(tmp_file.resolve(), "w") as f:
            yaml.dump(nebari_config, f)

        assert tmp_file.exists() is True
        app = create_cli()

        valid_result = runner.invoke(
            app,
            ["validate", "--config", tmp_file.resolve()],
            env={"NEBARI_SECRET__amazon_web_services__kubernetes_version": "1.20"},
        )

        assert 0 == valid_result.exit_code
        assert not valid_result.exception
        assert "Successfully validated configuration" in valid_result.stdout

        invalid_result = runner.invoke(
            app,
            ["validate", "--config", tmp_file.resolve()],
            env={"NEBARI_SECRET__amazon_web_services__kubernetes_version": "1.0"},
        )

        assert 1 == invalid_result.exit_code
        assert invalid_result.exception
        assert "Invalid `kubernetes-version`" in invalid_result.stdout


@pytest.mark.parametrize(
    "key, value, provider, expected_message, addl_config",
    [
        ("NEBARI_SECRET__project_name", "123invalid", "local", "validation error", {}),
        (
            "NEBARI_SECRET__this_is_an_error",
            "true",
            "local",
            "Object has no attribute",
            {},
        ),
        (
            "NEBARI_SECRET__amazon_web_services__kubernetes_version",
            "1.0",
            "aws",
            "validation error",
            {
                "amazon_web_services": {
                    "region": "us-east-1",
                    "kubernetes_version": "1.19",
                }
            },
        ),
    ],
)
def test_cli_validate_error_from_env(
    key: str,
    value: str,
    provider: str,
    expected_message: str,
    addl_config: Dict[str, Any],
):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        nebari_config = {
            **yaml.safe_load(
                f"""
provider: {provider}
project_name: test
        """
            ),
            **addl_config,
        }

        with open(tmp_file.resolve(), "w") as f:
            yaml.dump(nebari_config, f)

        assert tmp_file.exists() is True
        app = create_cli()

        # confirm the file is otherwise valid without environment variable overrides
        pre = runner.invoke(app, ["validate", "--config", tmp_file.resolve()])
        assert 0 == pre.exit_code
        assert not pre.exception

        # run validate again with environment variables that are expected to trigger
        # validation errors
        result = runner.invoke(
            app, ["validate", "--config", tmp_file.resolve()], env={key: value}
        )

        assert 1 == result.exit_code
        assert result.exception
        assert expected_message in result.stdout


@pytest.mark.parametrize(
    "provider, addl_config",
    [
        (
            "aws",
            {
                "amazon_web_services": {
                    "kubernetes_version": "1.20",
                    "region": "us-east-1",
                }
            },
        ),
        ("azure", {"azure": {"kubernetes_version": "1.20", "region": "Central US"}}),
        (
            "gcp",
            {
                "google_cloud_platform": {
                    "kubernetes_version": "1.20",
                    "region": "us-east1",
                    "project": "test",
                }
            },
        ),
        ("do", {"digital_ocean": {"kubernetes_version": "1.20", "region": "nyc3"}}),
        pytest.param(
            "local",
            {"security": {"authentication": {"type": "Auth0"}}},
            id="auth-provider-auth0",
        ),
        pytest.param(
            "local",
            {"security": {"authentication": {"type": "GitHub"}}},
            id="auth-provider-github",
        ),
    ],
)
def test_cli_validate_error_missing_cloud_env(
    monkeypatch: pytest.MonkeyPatch, provider: str, addl_config: Dict[str, Any]
):
    # cloud methods are all globally mocked, need to reset so the env variables will be checked
    monkeypatch.undo()
    for e in [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "GOOGLE_CREDENTIALS",
        "PROJECT_ID",
        "ARM_SUBSCRIPTION_ID",
        "ARM_TENANT_ID",
        "ARM_CLIENT_ID",
        "ARM_CLIENT_SECRET",
        "DIGITALOCEAN_TOKEN",
        "SPACES_ACCESS_KEY_ID",
        "SPACES_SECRET_ACCESS_KEY",
        "AUTH0_CLIENT_ID",
        "AUTH0_CLIENT_SECRET",
        "AUTH0_DOMAIN",
        "GITHUB_CLIENT_ID",
        "GITHUB_CLIENT_SECRET",
    ]:
        try:
            monkeypatch.delenv(e)
        except Exception:
            pass

    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        nebari_config = {
            **yaml.safe_load(
                f"""
provider: {provider}
project_name: test
        """
            ),
            **addl_config,
        }

        with open(tmp_file.resolve(), "w") as f:
            yaml.dump(nebari_config, f)

        assert tmp_file.exists() is True
        app = create_cli()

        result = runner.invoke(app, ["validate", "--config", tmp_file.resolve()])

        assert 1 == result.exit_code
        assert result.exception
        assert "Missing the following required environment variable" in result.stdout


def generate_test_data_test_cli_validate_error():
    """
    Search the cli_validate folder for unhappy path test cases
    and add them to the parameterized list of inputs for
    test_cli_validate_error. Optionally parse an expected
    error message from the file name to assert is present
    in the validate output
    """

    test_data = []
    for f in TEST_DATA_DIR.iterdir():
        if f.is_file():
            m = re.match(r"^\w*\.error\.([\w-]*)\.yaml$", f.name) or re.match(
                r"^\w*\.error\.([\w-]*)\.[\w-]*\.yaml$", f.name
            )  # sample.error.assert-message.optional-description.yaml
            if m:
                test_data.append((f.name, m.groups()[0]))
            elif re.match(r"^\w*\.error\.yaml$", f.name):  # sample.error.yaml
                test_data.append((f.name, None))
    keys = [
        "config_yaml",
        "expected_message",
    ]
    return {"keys": keys, "test_data": test_data}


def test_cli_validate_error(config_yaml: str, expected_message: str):
    test_file = TEST_DATA_DIR / config_yaml
    assert test_file.exists() is True

    app = create_cli()
    result = runner.invoke(app, ["validate", "--config", test_file])

    assert result.exception
    assert 1 == result.exit_code
    assert "ERROR validating configuration" in result.stdout
    if expected_message:
        # since this will usually come from a parsed filename, assume spacing/hyphenation/case is optional
        assert (expected_message in result.stdout.lower()) or (
            expected_message.replace("-", " ").replace("_", " ")
            in result.stdout.lower()
        )


def pytest_generate_tests(metafunc):
    """
    Dynamically generate test data parameters for test functions by looking for
    and executing an associated generate_test_data_{function_name} if one exists.
    """

    try:
        td = eval(f"generate_test_data_{metafunc.function.__name__}")()
        metafunc.parametrize(",".join(td["keys"]), td["test_data"])
    except Exception:
        # expected when a generate_test_data_ function doesn't exist
        pass
