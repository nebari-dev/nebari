import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml
from typer.testing import CliRunner

import _nebari.upgrade
import _nebari.version
from _nebari.cli import create_cli


# can't upgrade to a previous version that doesn't have a corresponding
# UpgradeStep derived class. without these dummy classes, the rendered
# nebari-config.yaml will have the wrong version
class Test_Cli_Upgrade_2022_10_1(_nebari.upgrade.UpgradeStep):
    version = "2022.10.1"


class Test_Cli_Upgrade_2022_11_1(_nebari.upgrade.UpgradeStep):
    version = "2022.11.1"


class Test_Cli_Upgrade_2023_1_1(_nebari.upgrade.UpgradeStep):
    version = "2023.1.1"


class Test_Cli_Upgrade_2023_4_1(_nebari.upgrade.UpgradeStep):
    version = "2023.4.1"


class Test_Cli_Upgrade_2023_5_1(_nebari.upgrade.UpgradeStep):
    version = "2023.5.1"


### end dummy upgrade classes

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
        # only used for old qhub version upgrades
        (
            ["--attempt-fixes"],
            2,
            ["Missing option"],
        ),
    ],
)
def test_upgrade_stdout(args: List[str], exit_code: int, content: List[str]):
    app = create_cli()
    result = runner.invoke(app, ["upgrade"] + args)
    assert result.exit_code == exit_code
    for c in content:
        assert c in result.stdout


def test_upgrade_2022_10_1_to_2022_11_1(monkeypatch: pytest.MonkeyPatch):
    assert_nebari_upgrade_success(monkeypatch, "2022.10.1", "2022.11.1")


def test_upgrade_2022_11_1_to_2023_1_1(monkeypatch: pytest.MonkeyPatch):
    assert_nebari_upgrade_success(monkeypatch, "2022.11.1", "2023.1.1")


def test_upgrade_2023_1_1_to_2023_4_1(monkeypatch: pytest.MonkeyPatch):
    assert_nebari_upgrade_success(monkeypatch, "2023.1.1", "2023.4.1")


def test_upgrade_2023_4_1_to_2023_5_1(monkeypatch: pytest.MonkeyPatch):
    assert_nebari_upgrade_success(
        monkeypatch,
        "2023.4.1",
        "2023.5.1",
        # Have you deleted the Argo Workflows CRDs and service accounts
        inputs=["y"],
    )


@pytest.mark.parametrize(
    "workflows_enabled, workflow_controller_enabled",
    [(True, True), (True, False), (False, None), (None, None)],
)
def test_upgrade_2023_5_1_to_2023_7_2(
    monkeypatch: pytest.MonkeyPatch,
    workflows_enabled: bool,
    workflow_controller_enabled: bool,
):
    addl_config = {}
    inputs = []

    if workflows_enabled is not None:
        addl_config = {"argo_workflows": {"enabled": workflows_enabled}}
        if workflows_enabled is True:
            inputs.append("y" if workflow_controller_enabled else "n")

    upgraded = assert_nebari_upgrade_success(
        monkeypatch,
        "2023.5.1",
        "2023.7.2",
        addl_config=addl_config,
        # Do you want to enable the Nebari Workflow Controller?
        inputs=inputs,
    )

    if workflows_enabled is True:
        if workflow_controller_enabled:
            assert (
                True
                is upgraded["argo_workflows"]["nebari_workflow_controller"]["enabled"]
            )
        else:
            # not sure this makes sense, the code defaults this to True if missing
            assert "nebari_workflow_controller" not in upgraded["argo_workflows"]
    elif workflows_enabled is False:
        assert False is upgraded["argo_workflows"]["enabled"]
    else:
        # argo_workflows config missing
        # this one doesn't sound right either, they default to true if this is missing, so why skip the questions?
        assert "argo_workflows" not in upgraded


def test_upgrade_image_tags(monkeypatch: pytest.MonkeyPatch):
    start_version = "2023.5.1"
    end_version = "2023.7.2"

    upgraded = assert_nebari_upgrade_success(
        monkeypatch,
        start_version,
        end_version,
        # # number of "y" inputs directly corresponds to how many matching images are found in yaml
        inputs=["y", "y", "y", "y", "y", "y", "y"],
        addl_config=yaml.safe_load(
            f"""
default_images:
  jupyterhub: quay.io/nebari/nebari-jupyterhub:{start_version}
  jupyterlab: quay.io/nebari/nebari-jupyterlab:{start_version}
  dask_worker: quay.io/nebari/nebari-dask-worker:{start_version}
profiles:
  jupyterlab:
  - display_name: base
    kubespawner_override:
      image: quay.io/nebari/nebari-jupyterlab:{start_version}
  - display_name: gpu
    kubespawner_override:
      image: quay.io/nebari/nebari-jupyterlab-gpu:{start_version}
  - display_name: any-other-version
    kubespawner_override:
      image: quay.io/nebari/nebari-jupyterlab:1955.11.5
  - display_name: leave-me-alone
    kubespawner_override:
      image: quay.io/nebari/leave-me-alone:{start_version}
  dask_worker:
  - display_name: dask-worker
    kubespawner_override:
      image: quay.io/nebari/nebari-dask-worker:{start_version}
"""
        ),
    )

    for _, v in upgraded["default_images"].items():
        assert v.endswith(end_version)
    for _, v in upgraded["profiles"].items():
        for profile in v:
            if profile["display_name"] != "leave-me-alone":
                # assume all other images should have been upgraded to the end_version
                assert profile["kubespawner_override"]["image"].endswith(end_version)
            else:
                # this one was selected not to match the regex for nebari images, should have been left alone
                assert profile["kubespawner_override"]["image"].endswith(start_version)


def test_upgrade_fail_on_downgrade(monkeypatch: pytest.MonkeyPatch):
    start_version = "2023.7.2"
    end_version = "2023.5.1"  # downgrade

    monkeypatch.setattr(_nebari.upgrade, "__version__", end_version)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        nebari_config = yaml.safe_load(
            f"""
project_name: test
provider: local
domain: test.example.com
namespace: dev
nebari_version: {start_version}
        """
        )

        with open(tmp_file.resolve(), "w") as f:
            yaml.dump(nebari_config, f)

        assert tmp_file.exists() is True
        app = create_cli()

        result = runner.invoke(app, ["upgrade", "--config", tmp_file.resolve()])

        # feels like this should return a non-zero exit code if the upgrade is not happening
        assert 0 == result.exit_code
        assert not result.exception
        assert "appears to be already up-to-date" in result.stdout

        # make sure the file is unaltered
        with open(tmp_file.resolve(), "r") as c:
            assert yaml.safe_load(c) == nebari_config


def assert_nebari_upgrade_success(
    monkeypatch: pytest.MonkeyPatch,
    start_version: str,
    end_version: str,
    addl_config: Dict[str, Any] = {},
    inputs: List[str] = [],
) -> Dict[str, Any]:
    monkeypatch.setattr(_nebari.upgrade, "__version__", end_version)

    # create a tmp dir and clean up when done
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        # merge basic config with any test case specific values provided
        nebari_config = {
            **yaml.safe_load(
                f"""
project_name: test
provider: local
domain: test.example.com
namespace: dev
nebari_version: {start_version}
        """
            ),
            **addl_config,
        }

        # write the test nebari-config.yaml file to tmp location
        with open(tmp_file.resolve(), "w") as f:
            yaml.dump(nebari_config, f)

        assert tmp_file.exists() is True
        app = create_cli()

        if inputs is not None and len(inputs) > 0:
            inputs += ""  # trailing newline for last input

        # run nebari upgrade -c tmp/nebari-config.yaml
        result = runner.invoke(
            app, ["upgrade", "--config", tmp_file.resolve()], input="\n".join(inputs)
        )

        assert 0 == result.exit_code
        assert not result.exception
        assert "Saving new config file" in result.stdout

        # load the modified nebari-config.yaml and check the new version has changed
        with open(tmp_file.resolve(), "r") as f:
            upgraded = yaml.safe_load(f)
            assert end_version == upgraded["nebari_version"]

        # check backup matches original
        backup_file = Path(tmp).resolve() / f"nebari-config.yaml.{start_version}.backup"
        assert backup_file.exists() is True
        with open(backup_file.resolve(), "r") as b:
            backup = yaml.safe_load(b)
            assert backup == nebari_config

        # pass the parsed nebari-config.yaml with upgrade mods back to caller for
        # additional assertions
        return upgraded
