import pytest
import requests

from _nebari.constants import AWS_ENV_DOCS, AZURE_ENV_DOCS, DO_ENV_DOCS, GCP_ENV_DOCS

LINKS_TO_TEST = [
    DO_ENV_DOCS,
    AWS_ENV_DOCS,
    GCP_ENV_DOCS,
    AZURE_ENV_DOCS,
]


@pytest.mark.parametrize("url,status_code", [(url, 200) for url in LINKS_TO_TEST])
def test_links(url, status_code):
    response = requests.get(url)
    assert response.status_code == status_code
