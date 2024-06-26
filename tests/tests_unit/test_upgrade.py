from contextlib import nullcontext
from pathlib import Path

import pytest
from rich.prompt import Prompt

from _nebari.upgrade import do_upgrade
from _nebari.version import __version__, rounded_ver_parse
from nebari.plugins import nebari_plugin_manager


@pytest.fixture
def qhub_users_import_json():
    return (
        (
            Path(__file__).parent
            / "./qhub-config-yaml-files-for-upgrade/qhub-users-import.json"
        )
        .read_text()
        .rstrip()
    )


@pytest.mark.parametrize(
    "old_qhub_config_path_str,attempt_fixes,expect_upgrade_error",
    [
        (
            "./qhub-config-yaml-files-for-upgrade/qhub-config-do-310.yaml",
            False,
            False,
        ),
        (
            "./qhub-config-yaml-files-for-upgrade/qhub-config-do-310-customauth.yaml",
            False,
            True,
        ),
        (
            "./qhub-config-yaml-files-for-upgrade/qhub-config-do-310-customauth.yaml",
            True,
            False,
        ),
    ],
)
def test_upgrade_4_0(
    old_qhub_config_path_str,
    attempt_fixes,
    expect_upgrade_error,
    tmp_path,
    qhub_users_import_json,
    monkeypatch,
):

    def mock_input(prompt, **kwargs):
        # Mock different upgrade steps prompt answers
        if (
            prompt
            == "Have you deleted the Argo Workflows CRDs and service accounts? [y/N] "
        ):
            return "y"
        elif (
            prompt
            == "\nDo you want Nebari to update the kube-prometheus-stack CRDs and delete the prometheus-node-exporter for you? If not, you'll have to do it manually."
        ):
            return "N"
        elif (
            prompt
            == "Have you backed up your custom dashboards (if necessary), deleted the prometheus-node-exporter daemonset and updated the kube-prometheus-stack CRDs?"
        ):
            return "y"
        # All other prompts will be answered with "y"
        else:
            return "y"

    monkeypatch.setattr(Prompt, "ask", mock_input)

    old_qhub_config_path = Path(__file__).parent / old_qhub_config_path_str

    tmp_qhub_config = Path(tmp_path, old_qhub_config_path.name)
    tmp_qhub_config.write_text(old_qhub_config_path.read_text())  # Copy contents to tmp

    orig_contents = tmp_qhub_config.read_text()  # Read in initial contents

    assert not Path(tmp_path, "qhub-users-import.json").exists()

    # Do the upgrade
    if not expect_upgrade_error:
        do_upgrade(
            tmp_qhub_config, attempt_fixes
        )  # Would raise an error if invalid by current Nebari version's standards
    else:
        with pytest.raises(ValueError):
            do_upgrade(tmp_qhub_config, attempt_fixes)
        return

    # Check the resulting YAML
    config = nebari_plugin_manager.read_config(tmp_qhub_config)

    assert len(config.security.keycloak.initial_root_password) == 16
    assert not hasattr(config.security, "users")
    assert not hasattr(config.security, "groups")

    __rounded_version__ = rounded_ver_parse(__version__)

    # Check image versions have been bumped up
    assert (
        config.default_images.jupyterhub
        == f"quansight/nebari-jupyterhub:v{__rounded_version__}"
    )
    assert (
        config.profiles.jupyterlab[0].kubespawner_override.image
        == f"quansight/nebari-jupyterlab:v{__rounded_version__}"
    )
    assert config.security.authentication.type != "custom"

    # Keycloak import users json
    assert (
        Path(tmp_path, "nebari-users-import.json").read_text().rstrip()
        == qhub_users_import_json
    )

    # Check backup
    tmp_qhub_config_backup = Path(tmp_path, f"{old_qhub_config_path.name}.old.backup")

    assert orig_contents == tmp_qhub_config_backup.read_text()


@pytest.mark.parametrize(
    "version_str, exception",
    [
        ("1.0.0", nullcontext()),
        ("1.cool.0", pytest.raises(ValueError, match=r"Invalid version string .*")),
        ("0,1.0", pytest.raises(ValueError, match=r"Invalid version string .*")),
        ("", pytest.raises(ValueError, match=r"Invalid version string .*")),
        (
            "1.0.0-rc1",
            pytest.raises(
                AssertionError,
                match=r"Invalid version .*: must be a full release version, not a dev/prerelease/postrelease version",
            ),
        ),
        (
            "1.0.0dev1",
            pytest.raises(
                AssertionError,
                match=r"Invalid version .*: must be a full release version, not a dev/prerelease/postrelease version",
            ),
        ),
    ],
)
def test_version_string(new_upgrade_cls, version_str, exception):
    with exception:

        class DummyUpgrade(new_upgrade_cls):
            version = version_str


def test_duplicated_version(new_upgrade_cls):
    duplicated_version = "1.2.3"
    with pytest.raises(
        AssertionError, match=rf"Duplicate UpgradeStep version {duplicated_version}"
    ):

        class DummyUpgrade(new_upgrade_cls):
            version = duplicated_version

        class DummyUpgrade2(new_upgrade_cls):
            version = duplicated_version

        class DummyUpgrade3(new_upgrade_cls):
            version = "1.2.4"
