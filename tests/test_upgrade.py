from pathlib import Path

import pytest

from nebari.upgrade import do_upgrade, load_yaml, verify
from nebari.version import __version__, rounded_ver_parse


@pytest.fixture
def nebari_users_import_json():
    return (
        (
            Path(__file__).parent
            / "./nebari-config-yaml-files-for-upgrade/nebari-users-import.json"
        )
        .read_text()
        .rstrip()
    )


@pytest.mark.parametrize(
    "old_nebari_config_path_str,attempt_fixes,expect_upgrade_error",
    [
        (
            "./nebari-config-yaml-files-for-upgrade/nebari-config-do-310.yaml",
            False,
            False,
        ),
        (
            "./nebari-config-yaml-files-for-upgrade/nebari-config-do-310-customauth.yaml",
            False,
            True,
        ),
        (
            "./nebari-config-yaml-files-for-upgrade/nebari-config-do-310-customauth.yaml",
            True,
            False,
        ),
    ],
)
def test_upgrade_4_0(
    old_nebari_config_path_str,
    attempt_fixes,
    expect_upgrade_error,
    tmp_path,
    nebari_users_import_json,
):
    old_nebari_config_path = Path(__file__).parent / old_nebari_config_path_str

    tmp_nebari_config = Path(tmp_path, old_nebari_config_path.name)
    tmp_nebari_config.write_text(
        old_nebari_config_path.read_text()
    )  # Copy contents to tmp

    orig_contents = tmp_nebari_config.read_text()  # Read in initial contents

    assert not Path(tmp_path, "nebari-users-import.json").exists()

    # Do the upgrade
    if not expect_upgrade_error:
        do_upgrade(
            tmp_nebari_config, attempt_fixes
        )  # Would raise an error if invalid by current nebari version's standards
    else:
        with pytest.raises(ValueError):
            do_upgrade(tmp_nebari_config, attempt_fixes)
        return

    # Check the resulting YAML
    config = load_yaml(tmp_nebari_config)

    verify(
        config
    )  # Would raise an error if invalid by current nebari version's standards

    assert len(config["security"]["keycloak"]["initial_root_password"]) == 16

    assert "users" not in config["security"]
    assert "groups" not in config["security"]

    __rounded_version__ = ".".join([str(c) for c in rounded_ver_parse(__version__)])

    # Check image versions have been bumped up
    assert (
        config["default_images"]["jupyterhub"]
        == f"quansight/nebari-jupyterhub:v{__rounded_version__}"
    )
    assert (
        config["profiles"]["jupyterlab"][0]["kubespawner_override"]["image"]
        == f"quansight/nebari-jupyterlab:v{__rounded_version__}"
    )

    assert (
        config.get("security", {}).get("authentication", {}).get("type", "") != "custom"
    )

    # Keycloak import users json
    assert (
        Path(tmp_path, "nebari-users-import.json").read_text().rstrip()
        == nebari_users_import_json
    )

    # Check backup
    tmp_nebari_config_backup = Path(
        tmp_path, f"{old_nebari_config_path.name}.old.backup"
    )

    assert orig_contents == tmp_nebari_config_backup.read_text()
