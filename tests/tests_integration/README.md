# Integration Testing via Pytest

These tests are designed to test things on Nebari deployed
on cloud.


## Digital Ocean

```bash
DIGITALOCEAN_TOKEN
NEBARI_K8S_VERSION
SPACES_ACCESS_KEY_ID
SPACES_SECRET_ACCESS_KEY
CLOUDFLARE_TOKEN
```

Once those are set, you can run:

```bash
pytest tests_integration -vvv -s -m do
```

This will deploy on Nebari on Amazon Web Services, run tests on the deployment
and then teardown the cluster.

## Amazon Web Services

```bash
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
CLOUDFLARE_TOKEN
```

Once those are set, you can run:

```bash
pytest tests_integration -vvv -s -m aws
```

This will deploy on Nebari on Amazon Web Services, run tests on the deployment
and then teardown the cluster.

## Amazon Web Services

```bash
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
CLOUDFLARE_TOKEN
```

Once those are set, you can run:

```bash
pytest tests_integration -vvv -s -m aws
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

```bash
pytest tests_integration -vvv -s -m azure
```
