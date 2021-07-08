import pytest
from qhub.deploy import check_secrets

def test_check_secrets(monkeypatch):

    # Should do nothing without prefect key
    check_secrets({"key":"value"})

    # Should do nothing if appropriate var is set
    monkeypatch.setenv("TF_VAR_prefect_token","secret_token")
    check_secrets({"prefect":"value"})

    # Should raise error if var is not set
    monkeypatch.delenv("TF_VAR_prefect_token")
    with pytest.raises(EnvironmentError):
        check_secrets({"prefect":"value"})

