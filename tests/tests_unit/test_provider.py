from contextlib import nullcontext

import pytest

from _nebari.provider.cloud.google_cloud import check_missing_service


@pytest.mark.parametrize(
    "activated_services, exception",
    [
        (
            {
                "Compute Engine API",
                "Kubernetes Engine API",
                "Cloud Monitoring API",
                "Cloud Autoscaling API",
                "Identity and Access Management (IAM) API",
                "Cloud Resource Manager API",
            },
            nullcontext(),
        ),
        (
            {
                "Compute Engine API",
                "Kubernetes Engine API",
                "Cloud Monitoring API",
                "Cloud Autoscaling API",
                "Identity and Access Management (IAM) API",
                "Cloud Resource Manager API",
                "Cloud SQL Admin API",
            },
            nullcontext(),
        ),
        (
            {
                "Compute Engine API",
                "Kubernetes Engine API",
                "Cloud Monitoring API",
                "Cloud Autoscaling API",
                "Cloud SQL Admin API",
            },
            pytest.raises(ValueError, match=r"Missing required services:.*"),
        ),
    ],
)
def test_gcp_missing_service(monkeypatch, activated_services, exception):
    def mock_return():
        return activated_services

    monkeypatch.setattr(
        "_nebari.provider.cloud.google_cloud.activated_services", mock_return
    )
    with exception:
        check_missing_service()
