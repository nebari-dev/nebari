from unittest.mock import patch

import pytest
from packaging.requirements import SpecifierSet

from _nebari.config_set import ConfigSetMetadata, read_config_set

test_version = "2024.12.2"


@pytest.mark.parametrize(
    "version_input,test_version,should_pass",
    [
        # Standard version tests
        (">=2024.12.0,<2025.0.0", "2024.12.2", True),
        (SpecifierSet(">=2024.12.0,<2025.0.0"), "2024.12.2", True),
        # Pre-release version requirement tests
        (">=2024.12.0rc1,<2025.0.0", "2024.12.0rc1", True),
        (SpecifierSet(">=2024.12.0rc1"), "2024.12.0rc2", True),
        # Pre-release test version against standard requirement
        (">=2024.12.0,<2025.0.0", "2024.12.1rc1", True),
        (SpecifierSet(">=2024.12.0,<2025.0.0"), "2024.12.1rc1", True),
        # Failing cases
        (">=2025.0.0", "2024.12.2rc1", False),
        (SpecifierSet(">=2025.0.0rc1"), "2024.12.2", False),
    ],
)
def test_version_requirement(version_input, test_version, should_pass):
    metadata = ConfigSetMetadata(name="test-config", nebari_version=version_input)

    if should_pass:
        metadata.check_version(test_version)
    else:
        with pytest.raises(ValueError) as exc_info:
            metadata.check_version(test_version)
        assert "Nebari version" in str(exc_info.value)


def test_read_config_set_valid(tmp_path):
    config_set_yaml = """
    metadata:
      name: test-config
      nebari_version: ">=2024.12.0"
    config:
      key: value
    """
    config_set_filepath = tmp_path / "config_set.yaml"
    config_set_filepath.write_text(config_set_yaml)
    with patch("_nebari.config_set.__version__", "2024.12.2"):
        config_set = read_config_set(str(config_set_filepath))
    assert config_set.metadata.name == "test-config"
    assert config_set.config["key"] == "value"


def test_read_config_set_invalid_version(tmp_path):
    config_set_yaml = """
    metadata:
      name: test-config
      nebari_version: ">=2025.0.0"
    config:
      key: value
    """
    config_set_filepath = tmp_path / "config_set.yaml"
    config_set_filepath.write_text(config_set_yaml)

    with patch("_nebari.config_set.__version__", "2024.12.2"):
        with pytest.raises(ValueError) as exc_info:
            read_config_set(str(config_set_filepath))
        assert "Nebari version" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main()
