import urllib

from _nebari.provider import terraform


def test_terraform_open_source_license():
    tf_version = terraform.version()
    license_url = (
        f"https://raw.githubusercontent.com/hashicorp/terraform/v{tf_version}/LICENSE"
    )

    request = urllib.request.Request(license_url)
    with urllib.request.urlopen(request) as response:
        assert 200 == response.getcode()

        license = str(response.read())
        assert "Mozilla Public License" in license
        assert "Business Source License" not in license
