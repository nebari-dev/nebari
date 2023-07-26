# Integration Testing via Pytest

These tests are designed to test things on Nebari deployed
on cloud. At the moment it only deploys on DigitalOcean.

You need the following environment variables to run these.

```bash
DIGITALOCEAN_TOKEN
NEBARI_K8S_VERSION
SPACES_ACCESS_KEY_ID
SPACES_SECRET_ACCESS_KEY
CLOUDFLARE_TOKEN
```

For instructions on how to get these variables check the documentation
for DigitalOcean deployment.

Running Tests:

```bash
pytest tests_integration -vvv -s
```

This would deploy on digitalocean, run tests on the deployment
and then teardown the cluster.
