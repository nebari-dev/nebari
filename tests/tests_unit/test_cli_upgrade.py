import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml
from typer.testing import CliRunner

import _nebari.upgrade
from _nebari.cli import create_cli
from _nebari.constants import AZURE_DEFAULT_REGION
from _nebari.upgrade import UPGRADE_KUBERNETES_MESSAGE
from _nebari.utils import get_provider_config_block_name
from _nebari.version import rounded_ver_parse

MOCK_KUBERNETES_VERSIONS = {
    "aws": ["1.20"],
    "azure": ["1.20"],
    "gcp": ["1.20"],
    "do": ["1.21.5-do.0"],
}
MOCK_CLOUD_REGIONS = {
    "aws": ["us-east-1"],
    "azure": [AZURE_DEFAULT_REGION],
    "gcp": ["us-central1"],
    "do": ["nyc3"],
}


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
def test_cli_upgrade_stdout(args: List[str], exit_code: int, content: List[str]):
    app = create_cli()
    result = runner.invoke(app, ["upgrade"] + args)
    assert result.exit_code == exit_code
    for c in content:
        assert c in result.stdout


def test_cli_upgrade_2022_10_1_to_2022_11_1(monkeypatch: pytest.MonkeyPatch):
    assert_nebari_upgrade_success(monkeypatch, "2022.10.1", "2022.11.1")


def test_cli_upgrade_2022_11_1_to_2023_1_1(monkeypatch: pytest.MonkeyPatch):
    assert_nebari_upgrade_success(monkeypatch, "2022.11.1", "2023.1.1")


def test_cli_upgrade_2023_1_1_to_2023_4_1(monkeypatch: pytest.MonkeyPatch):
    assert_nebari_upgrade_success(monkeypatch, "2023.1.1", "2023.4.1")


def test_cli_upgrade_2023_4_1_to_2023_5_1(monkeypatch: pytest.MonkeyPatch):
    assert_nebari_upgrade_success(
        monkeypatch,
        "2023.4.1",
        "2023.5.1",
        # Have you deleted the Argo Workflows CRDs and service accounts
        inputs=["y"],
    )


@pytest.mark.parametrize(
    "provider",
    ["aws", "azure", "do", "gcp"],
)
def test_cli_upgrade_2023_5_1_to_2023_7_1(
    monkeypatch: pytest.MonkeyPatch, provider: str
):
    config = assert_nebari_upgrade_success(
        monkeypatch, "2023.5.1", "2023.7.1", provider=provider
    )
    prevent_deploy = config.get("prevent_deploy")
    if provider == "aws":
        assert prevent_deploy
    else:
        assert not prevent_deploy


@pytest.mark.parametrize(
    "workflows_enabled, workflow_controller_enabled",
    [(True, True), (True, False), (False, None), (None, None)],
)
def test_cli_upgrade_2023_7_1_to_2023_7_2(
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
        "2023.7.1",
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


def test_cli_upgrade_image_tags(monkeypatch: pytest.MonkeyPatch):
    start_version = "2023.5.1"
    end_version = "2023.7.1"

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
    test:
      image: quay.io/nebari/nebari-dask-worker:{start_version}
"""
        ),
    )

    for _, v in upgraded["default_images"].items():
        assert v.endswith(end_version)

    for profile in upgraded["profiles"]["jupyterlab"]:
        if profile["display_name"] != "leave-me-alone":
            # assume all other images should have been upgraded to the end_version
            assert profile["kubespawner_override"]["image"].endswith(end_version)
        else:
            # this one was selected not to match the regex for nebari images, should have been left alone
            assert profile["kubespawner_override"]["image"].endswith(start_version)

    for _, profile in upgraded["profiles"]["dask_worker"].items():
        assert profile["image"].endswith(end_version)


def test_cli_upgrade_fail_on_missing_file():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        app = create_cli()

        result = runner.invoke(app, ["upgrade", "--config", tmp_file.resolve()])

        assert 1 == result.exit_code
        assert result.exception
        assert (
            f"passed in configuration filename={tmp_file.resolve()} must exist"
            in str(result.exception)
        )


def test_cli_upgrade_fail_on_downgrade():
    start_version = "9999.9.9"  # way in the future
    end_version = _nebari.upgrade.__version__

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

        assert 1 == result.exit_code
        assert result.exception
        assert (
            f"already belongs to a later version ({start_version}) than the installed version of Nebari ({end_version})"
            in str(result.exception)
        )

        # make sure the file is unaltered
        with open(tmp_file.resolve(), "r") as c:
            assert yaml.safe_load(c) == nebari_config


def test_cli_upgrade_does_nothing_on_same_version():
    # this test only seems to work against the actual current version, any
    # mocked earlier versions trigger an actual update
    start_version = _nebari.upgrade.__version__

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
        assert "up-to-date" in result.stdout

        # make sure the file is unaltered
        with open(tmp_file.resolve(), "r") as c:
            assert yaml.safe_load(c) == nebari_config


def test_cli_upgrade_0_3_12_to_0_4_0(monkeypatch: pytest.MonkeyPatch):
    start_version = "0.3.12"
    end_version = "0.4.0"

    def callback(tmp_file: Path, _result: Any):
        users_import_file = tmp_file.parent / "nebari-users-import.json"
        assert users_import_file.exists()

        return True  # continue with default assertions

    # custom authenticators removed in 0.4.0, should be replaced by password
    upgraded = assert_nebari_upgrade_success(
        monkeypatch,
        start_version,
        end_version,
        addl_args=["--attempt-fixes"],
        addl_config=yaml.safe_load(
            """
security:
  authentication:
    type: custom
    config:
      oauth_callback_url: ""
      scope: ""
  users: {}
  groups:
    users: {}
terraform_modules: []
default_images:
  conda_store: ""
  dask_gateway: ""
"""
        ),
        callback=callback,
    )

    assert "password" == upgraded["security"]["authentication"]["type"]
    assert "" != upgraded["security"]["keycloak"]["initial_root_password"]
    assert "users" not in upgraded["security"]
    assert "groups" not in upgraded["security"]
    assert "config" not in upgraded["security"]["authentication"]
    assert True is upgraded["security"]["shared_users_group"]
    assert "terraform_modules" not in upgraded
    assert {} == upgraded["default_images"]
    assert True is upgraded["prevent_deploy"]


def test_cli_upgrade_to_0_4_0_fails_for_custom_auth_without_attempt_fixes():
    start_version = "0.3.12"

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
security:
  authentication:
    type: custom
        """
        )

        with open(tmp_file.resolve(), "w") as f:
            yaml.dump(nebari_config, f)

        assert tmp_file.exists() is True
        app = create_cli()

        result = runner.invoke(app, ["upgrade", "--config", tmp_file.resolve()])

        assert 1 == result.exit_code
        assert result.exception
        assert "Custom Authenticators are no longer supported" in str(result.exception)

        # make sure the file is unaltered
        with open(tmp_file.resolve(), "r") as c:
            assert yaml.safe_load(c) == nebari_config


@pytest.mark.skipif(
    rounded_ver_parse(_nebari.upgrade.__version__) < rounded_ver_parse("2023.10.1"),
    reason="This test is only valid for versions >= 2023.10.1",
)
def test_cli_upgrade_to_2023_10_1_cdsdashboard_removed(monkeypatch: pytest.MonkeyPatch):
    start_version = "2023.7.2"
    end_version = "2023.10.1"

    addl_config = yaml.safe_load(
        """
cdsdashboards:
  enabled: true
  cds_hide_user_named_servers: true
  cds_hide_user_dashboard_servers: false
        """
    )

    upgraded = assert_nebari_upgrade_success(
        monkeypatch,
        start_version,
        end_version,
        addl_args=["--attempt-fixes"],
        addl_config=addl_config,
    )

    assert not upgraded.get("cdsdashboards")
    assert upgraded.get("prevent_deploy")


@pytest.mark.skipif(
    rounded_ver_parse(_nebari.upgrade.__version__) < rounded_ver_parse("2023.10.1"),
    reason="This test is only valid for versions >= 2023.10.1",
)
@pytest.mark.parametrize(
    ("provider", "k8s_status"),
    [
        ("aws", "compatible"),
        ("aws", "incompatible"),
        ("aws", "invalid"),
        ("azure", "compatible"),
        ("azure", "incompatible"),
        ("azure", "invalid"),
        ("do", "compatible"),
        ("do", "incompatible"),
        ("do", "invalid"),
        ("gcp", "compatible"),
        ("gcp", "incompatible"),
        ("gcp", "invalid"),
    ],
)
def test_cli_upgrade_to_2023_10_1_kubernetes_validations(
    monkeypatch: pytest.MonkeyPatch, provider: str, k8s_status: str
):
    start_version = "2023.7.2"
    end_version = "2023.10.1"
    monkeypatch.setattr(_nebari.upgrade, "__version__", end_version)

    kubernetes_configs = {
        "aws": {"incompatible": "1.19", "compatible": "1.26", "invalid": "badname"},
        "azure": {"incompatible": "1.23", "compatible": "1.26", "invalid": "badname"},
        "do": {
            "incompatible": "1.19.2-do.3",
            "compatible": "1.26.0-do.custom",
            "invalid": "badname",
        },
        "gcp": {"incompatible": "1.23", "compatible": "1.26", "invalid": "badname"},
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp).resolve() / "nebari-config.yaml"
        assert tmp_file.exists() is False

        nebari_config = yaml.safe_load(
            f"""
project_name: test
provider: {provider}
domain: test.example.com
namespace: dev
nebari_version: {start_version}
cdsdashboards:
  enabled: true
  cds_hide_user_named_servers: true
  cds_hide_user_dashboard_servers: false
{get_provider_config_block_name(provider)}:
    region: {MOCK_CLOUD_REGIONS.get(provider, {})[0]}
    kubernetes_version: {kubernetes_configs[provider][k8s_status]}
        """
        )
        with open(tmp_file.resolve(), "w") as f:
            yaml.dump(nebari_config, f)

            assert tmp_file.exists() is True
            app = create_cli()

            result = runner.invoke(app, ["upgrade", "--config", tmp_file.resolve()])

            if k8s_status == "incompatible":
                UPGRADE_KUBERNETES_MESSAGE_WO_BRACKETS = re.sub(
                    r"\[.*?\]", "", UPGRADE_KUBERNETES_MESSAGE
                )
                assert UPGRADE_KUBERNETES_MESSAGE_WO_BRACKETS in result.stdout.replace(
                    "\n", ""
                )

            if k8s_status == "compatible":
                assert 0 == result.exit_code
                assert not result.exception
                assert "Saving new config file" in result.stdout

                # load the modified nebari-config.yaml and check the new version has changed
                with open(tmp_file.resolve(), "r") as f:
                    upgraded = yaml.safe_load(f)
                    assert end_version == upgraded["nebari_version"]

            if k8s_status == "invalid":
                assert (
                    "Unable to detect Kubernetes version for provider {}".format(
                        provider
                    )
                    in result.stdout
                )


def assert_nebari_upgrade_success(
    monkeypatch: pytest.MonkeyPatch,
    start_version: str,
    end_version: str,
    provider: str = "local",
    addl_args: List[str] = [],
    addl_config: Dict[str, Any] = {},
    inputs: List[str] = [],
    callback: Any = None,
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
provider: {provider}
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
            inputs.append("")  # trailing newline for last input

        # run nebari upgrade -c tmp/nebari-config.yaml
        result = runner.invoke(
            app,
            ["upgrade", "--config", tmp_file.resolve()] + addl_args,
            input="\n".join(inputs),
        )

        enable_default_assertions = True

        if callback is not None:
            enable_default_assertions = callback(tmp_file, result)

        if enable_default_assertions:
            assert 0 == result.exit_code
            assert not result.exception
            assert "Saving new config file" in result.stdout

            # load the modified nebari-config.yaml and check the new version has changed
            with open(tmp_file.resolve(), "r") as f:
                upgraded = yaml.safe_load(f)
                assert end_version == upgraded["nebari_version"]

            # check backup matches original
            backup_file = (
                Path(tmp).resolve() / f"nebari-config.yaml.{start_version}.backup"
            )
            assert backup_file.exists() is True
            with open(backup_file.resolve(), "r") as b:
                backup = yaml.safe_load(b)
                assert backup == nebari_config

        # pass the parsed nebari-config.yaml with upgrade mods back to caller for
        # additional assertions
        return upgraded
