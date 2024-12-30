from unittest.mock import patch

import pytest
from packaging.requirements import Requirement

from _nebari.config_set import ConfigSetMetadata, read_config_set

test_version = "2024.12.2"


test_version = "2024.12.2"


@pytest.mark.parametrize(
    "version_input,should_pass",
    [
        (">=2024.12.0,<2025.0.0", True),
        (Requirement("nebari>=2024.12.0,<2025.0.0"), True),
        (">=2025.0.0", False),
        (Requirement("nebari>=2025.0.0"), False),
    ],
)
def test_version_requirement(version_input, should_pass):
    metadata = ConfigSetMetadata(name="test-config", nebari_version=version_input)

    if should_pass:
        metadata.check_version(test_version)
    else:
        with pytest.raises(ValueError) as exc_info:
            metadata.check_version(test_version)
        assert "Current Nebari version" in str(exc_info.value)


def test_valid_version_requirement_with_requirement_object():
    requirement = Requirement("nebari>=2024.12.0")
    metadata = ConfigSetMetadata(name="test-config", nebari_version=requirement)
    assert metadata.nebari_version.specifier.contains(test_version)


def test_invalid_version_requirement_with_requirement_object():
    requirement = Requirement("nebari>=2025.0.0")
    with pytest.raises(ValueError) as exc_info:
        csm = ConfigSetMetadata(name="test-config", nebari_version=requirement)
        csm.check_version(test_version)
    assert "Current Nebari version" in str(exc_info.value)


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
        assert "Current Nebari version" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main()
