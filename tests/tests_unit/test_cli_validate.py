import re
from pathlib import Path
from typing import List

import pytest
from typer.testing import CliRunner

from _nebari.cli import create_cli

TEST_DATA_DIR = Path(__file__).resolve().parent / "cli_validate"

MOCK_ENV = {
    k: "test"
    for k in [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",  # aws
        "GOOGLE_CREDENTIALS",
        "PROJECT_ID",  # gcp
        "ARM_SUBSCRIPTION_ID",
        "ARM_TENANT_ID",
        "ARM_CLIENT_ID",
        "ARM_CLIENT_SECRET",  # azure
        "DIGITALOCEAN_TOKEN",
        "SPACES_ACCESS_KEY_ID",
        "SPACES_SECRET_ACCESS_KEY",  # digital ocean
    ]
}

runner = CliRunner()


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
def test_validate_stdout(args: List[str], exit_code: int, content: List[str]):
    app = create_cli()
    result = runner.invoke(app, ["validate"] + args)
    assert result.exit_code == exit_code
    for c in content:
        assert c in result.stdout


def generate_test_data_test_validate_local_happy_path():
    test_data = []
    for f in TEST_DATA_DIR.iterdir():
        if f.is_file() and re.match(r"^\w*\.happy\.yaml$", f.name):  # sample.happy.yaml
            test_data.append((f.name))
    keys = [
        "config_yaml",
    ]
    return {"keys": keys, "test_data": test_data}


def test_validate_local_happy_path(config_yaml: str):
    test_file = TEST_DATA_DIR / config_yaml
    assert test_file.exists() is True

    app = create_cli()
    result = runner.invoke(app, ["validate", "--config", test_file], env=MOCK_ENV)
    assert not result.exception
    assert 0 == result.exit_code
    assert "Successfully validated configuration" in result.stdout


def generate_test_data_test_validate_error():
    test_data = []
    for f in TEST_DATA_DIR.iterdir():
        if f.is_file():
            m = re.match(
                r"^\w*\.error\.([\w-]*)\.yaml$", f.name
            )  # sample.error.message.yaml
            if m:
                test_data.append((f.name, m.groups()[0]))
            elif re.match(r"^\w*\.error\.yaml$", f.name):  # sample.error.yaml
                test_data.append((f.name, None))
    keys = [
        "config_yaml",
        "expected_message",
    ]
    return {"keys": keys, "test_data": test_data}


def test_validate_error(config_yaml: str, expected_message: str):
    test_file = TEST_DATA_DIR / config_yaml
    assert test_file.exists() is True

    app = create_cli()
    result = runner.invoke(app, ["validate", "--config", test_file], env=MOCK_ENV)
    print(result.stdout)
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
