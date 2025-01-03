from typing import List
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from _nebari.cli import create_cli

runner = CliRunner()


@pytest.mark.parametrize(
    "args, exit_code, content",
    [
        # --help
        ([], 0, ["Usage:"]),
        (["--help"], 0, ["Usage:"]),
        (["-h"], 0, ["Usage:"]),
        (["list", "--help"], 0, ["Usage:"]),
        (["list", "-h"], 0, ["Usage:"]),
        (["list"], 0, ["Plugins"]),
    ],
)
def test_cli_plugin_stdout(args: List[str], exit_code: int, content: List[str]):
    app = create_cli()
    result = runner.invoke(app, ["plugin"] + args)
    assert result.exit_code == exit_code
    for c in content:
        assert c in result.stdout


def mock_get_plugins():
    mytestexternalplugin = Mock()
    mytestexternalplugin.__name__ = "mytestexternalplugin"

    otherplugin = Mock()
    otherplugin.__name__ = "otherplugin"

    return [mytestexternalplugin, otherplugin]


def mock_version(pkg):
    pkg_version_map = {
        "mytestexternalplugin": "0.4.4",
        "otherplugin": "1.1.1",
    }
    return pkg_version_map.get(pkg)


@patch(
    "nebari.plugins.NebariPluginManager.plugin_manager.get_plugins", mock_get_plugins
)
@patch("_nebari.subcommands.plugin.version", mock_version)
def test_cli_plugin_list_external_plugins():
    app = create_cli()
    result = runner.invoke(app, ["plugin", "list"])
    assert result.exit_code == 0
    expected_output = [
        "Plugins",
        "mytestexternalplugin │ 0.4.4",
        "otherplugin          │ 1.1.1",
    ]
    for c in expected_output:
        assert c in result.stdout
