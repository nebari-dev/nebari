import pytest
from qhub.deploy import check_secrets


def test_check_secrets(monkeypatch):

    # Should do nothing without prefect key or not enabled
    check_secrets({"key": "value"})
    check_secrets({"prefect": {"enabled": False}})

    # Should do nothing if appropriate var is set
    monkeypatch.setenv("TF_VAR_prefect_token", "secret_token")
    check_secrets({"prefect": {"enabled": True}})

    # Should raise error if var is not set
    monkeypatch.delenv("TF_VAR_prefect_token")
    with pytest.raises(EnvironmentError):
        check_secrets({"prefect": {"enabled": True}})
