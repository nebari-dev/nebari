# Integration Testing via Pytest

These tests are designed to test things on Nebari deployed
on cloud.

## Amazon Web Services

```bash
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
CLOUDFLARE_TOKEN
```

Assuming you're in the `tests_integration` directory, run:

```bash
pytest -vvv -s --cloud aws
```

This will deploy on Nebari on Amazon Web Services, run tests on the deployment
and then teardown the cluster.


## Azure

```bash
ARM_SUBSCRIPTION_ID
ARM_TENANT_ID
ARM_CLIENT_ID
ARM_CLIENT_SECRET
CLOUDFLARE_TOKEN
```

Assuming you're in the `tests_integration` directory, run:

```bash
pytest -vvv -s --cloud azure
```

This will deploy on Nebari on Azure, run tests on the deployment
and then teardown the cluster.
