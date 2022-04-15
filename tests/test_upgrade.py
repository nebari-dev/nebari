from pathlib import Path

import pytest

from qhub.upgrade import do_upgrade, load_yaml, verify
from qhub.version import __version__, rounded_ver_parse


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
        ("./qhub-config-yaml-files-for-upgrade/qhub-config-do-310.yaml", False, False),
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
):
    old_qhub_config_path = Path(__file__).parent / old_qhub_config_path_str

    tmp_qhub_config = Path(tmp_path, old_qhub_config_path.name)
    tmp_qhub_config.write_text(old_qhub_config_path.read_text())  # Copy contents to tmp

    orig_contents = tmp_qhub_config.read_text()  # Read in initial contents

    assert not Path(tmp_path, "qhub-users-import.json").exists()

    # Do the upgrade
    if not expect_upgrade_error:
        do_upgrade(
            tmp_qhub_config, attempt_fixes
        )  # Would raise an error if invalid by current QHub version's standards
    else:
        with pytest.raises(ValueError):
            do_upgrade(tmp_qhub_config, attempt_fixes)
        return

    # Check the resulting YAML
    config = load_yaml(tmp_qhub_config)

    verify(
        config
    )  # Would raise an error if invalid by current QHub version's standards

    assert len(config["security"]["keycloak"]["initial_root_password"]) == 16

    assert "users" not in config["security"]
    assert "groups" not in config["security"]

    __rounded_version__ = ".".join([str(c) for c in rounded_ver_parse(__version__)])

    # Check image versions have been bumped up
    assert (
        config["default_images"]["jupyterhub"]
        == f"quansight/qhub-jupyterhub:v{__rounded_version__}"
    )
    assert (
        config["profiles"]["jupyterlab"][0]["kubespawner_override"]["image"]
        == f"quansight/qhub-jupyterlab:v{__rounded_version__}"
    )

    assert (
        config.get("security", {}).get("authentication", {}).get("type", "") != "custom"
    )

    # Keycloak import users json
    assert (
        Path(tmp_path, "qhub-users-import.json").read_text().rstrip()
        == qhub_users_import_json
    )

    # Check backup
    tmp_qhub_config_backup = Path(tmp_path, f"{old_qhub_config_path.name}.old.backup")

    assert orig_contents == tmp_qhub_config_backup.read_text()
