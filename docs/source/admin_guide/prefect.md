# Prefect

Prefect is a workflow automation system. QHub integrates Prefect with a
feature flag as follows (in the top level):

```yaml
prefect:
  enabled: true
```

You can also specify a particular image for Prefect with the `image` key as follows:

```yaml
prefect:
  enabled: true
  image: prefecthq/prefect:0.14.22-python3.8
```

There are a bunch of components in getting Prefect working for you, here
is a brief description of them:

1. Create a free Prefect cloud account here: https://cloud.prefect.io/
2. Create a Service Account and an API key for the same and add this to the CI secrets as `TF_VAR_prefect_token`:
   - In GitHub: Set it in Secrets (https://docs.github.com/en/actions/reference/encrypted-secrets#creating-encrypted-secrets-for-a-repository)
   - In GitLab: Set it as Variables (https://docs.gitlab.com/ee/ci/variables/#gitlab-cicd-variables)
3. Create a project in the Prefect Cloud Dashboard. Alternatively from CLI:

```
prefect create project 'your-prefect-project-name'
```

The `TF_VAR_prefect_token` API key is set as `PREFECT__CLOUD__AGENT__AUTH_TOKEN`
environment variable in the agent. It is used while deploying Prefect Agent so that
it can connect to Prefect Cloud and query flows.

## Prefect Cloud

Prefect Cloud is a fully hosted, production-ready backend for Prefect Core.
Checkout [prefect documentation](https://docs.prefect.io/orchestration/#prefect-cloud)
to know more.


## Prefect Agent

Prefect Agents is a lightweight processes for orchestrating flow runs. Agents
run inside a user's architecture, and are responsible for starting and monitoring
flow runs.

During operation the agent process queries the Prefect API for any scheduled flow
runs, and allocates resources for them on their respective deployment platforms.

When you enable prefect via `qhub-config.yml` prefect agent is deployed on the
QHub's kubernetes cluster, which querys the Prefect Cloud for flow runs.

## Agent configuration overrides
You can override your agent configuration without having to modify the helm files directly.  The extra variable `overrides` makes this
possible by changing the default values for the Agent chart according to the settings presented on your qhub-config.yaml file.

The current variables, originaly available in the [Agent helm chart](https://github.com/PrefectHQ/server/blob/master/helm/prefect-server/templates/agent/deployment.yaml) that can be overridden include:

```
- IMAGE_PULL_SECRETS
- PREFECT__CLOUD__AGENT__LABELS
- JOB_MEM_REQUEST
- JOB_MEM_LIMIT
- JOB_CPU_REQUEST
- JOB_CPU_LIMIT
- IMAGE_PULL_POLICY
```

For example, if you just want to override the amount of CPU limits for each job, you would need to craft a declarative configuration,
in you qhub-config.yaml file, as follows:

```yaml
prefect:
 enabled: true
 overrides:
     prefect_agent:
       job:
         resources:
           limit:
             cpu: 4
```
Also, if you would like to include an extra variable to the agent environment configuration, that was not previcosly in the helm chart, you can do it by including it under
the `envVars` field in the overrides block. For example, if you would like to add `MY_VAR: "<value>"` to you agent environment, you can do so by adding the following to your qhub-config

```yaml
prefect:
 enabled: true
 overrides:
     envVars:
       MY_VAR: "<value>"
```
### Adding secrets to you Agent configuration
Overrides also allow you to define extra secrets to pass through your agent configuration, for example, when using [default secrets](https://docs.prefect.io/core/concepts/secrets.html#default-secrets) to automatically authenticate your flow with the listed service. In the Google cloud case, for `GCP_CREDENTIALS` context secret, you can do it by adding that specific key value pair into your configuration:

```yaml
prefect:
 enabled: true
 overrides:
   secretEnvVars:
       PREFECT__CONTEXT__SECRETS__GCP_CREDENTIALS: '<Your value>'
```
This secret will then be stored as a [kubernetes secret](https://kubernetes.io/docs/concepts/configuration/secret/) variable into you QHub secrets volume.

## Flows

Prefect agent can only orchestrate your flows, you need an actual flow to run via
prefect agent. The API for the same can be found in the [prefect documentation](https://docs.prefect.io/core/concepts/flows.html)
Here is a simple example from their official doc:

```python
from prefect import task, Task, Flow
import random

@task
def random_number():
    return random.randint(0, 100)

@task
def plus_one(x):
    return x + 1

with Flow('My Functional Flow') as flow:
    r = random_number()
    y = plus_one(x=r)
```

## Storage

The Prefect Storage interface encapsulates logic for storing flows. Each storage
unit is able to store multiple flows (with the constraint of name uniqueness within a given unit).

The API  documentation for the same can be found in the [prefect documentation](https://docs.prefect.io/api/latest/storage.html#docker)

## Example: Creating, Building and Register Flow

Below is a complete example of

- creating couple of workflows
- Adding them to a storage (docker in this case)
- Building and pushing that storage to a docker registry
- Registering the flows to prefect cloud

```python
import logging
import time

import prefect
from prefect import Flow, task
from prefect.storage import Docker


PREFECT_PROJECT = "your-prefect-project-name"
# Name of  your docker repository
DOCKER_REGISTRY = "quansight"


@task
def hello_world():
    """Sample flow to make sure prefect works."""
    logger = prefect.context.get("logger")
    logger.info("Running Hello World!")


def init_and_register_flows():
    storage = Docker(
        image_name="my-prefect-flows",
        image_tag=f"{time.time_ns()}",
        registry_url=DOCKER_REGISTRY,
        base_image="python:3.8",
        env_vars={
            "env_var": "value"
        },
    )
    prefect_flows = [
        Flow(
            name="hello-world-flow-1",
            tasks=[hello_world],
            storage=storage,
        ),
        Flow(
            name="hello-world-flow-2",
            tasks=[hello_world],
            storage=storage,
        ),
    ]

    add_flows_to_storage(storage, prefect_flows)
    storage.build()
    register_flows(prefect_flows, build=False)
    logging.info("Everything done.!")


def add_flows_to_storage(storage, flows):
    logging.info(f"Add flows: {flows} to storage: {storage}")
    flow_storage_paths = [storage.add_flow(flow) for flow in flows]
    logging.info(f"flows path in storage: {flow_storage_paths}")
    return storage


def register_flows(flows, **kwargs):
    logging.info(f"Registering flows: {flows}")
    registered_flows = [
        flow.register(project_name=PREFECT_PROJECT, **kwargs) for flow in flows
    ]
    logging.info(f"Registered flows: {registered_flows}")
    return registered_flows


def setup_logging(level=logging.INFO):
    """Setup standard logging format."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)9s %(lineno)4s %(module)s: %(message)s"
    )


def main():
    setup_logging()
    init_and_register_flows()


if __name__ == "__main__":
    main()
```

## Running your flows

Now that you have Prefect Agent running in QHub Kubernetes cluster, you
can now run your flows from either of the two ways:

- Triggering manually from the Prefect Cloud dashboard.
- Running them on a schedule by adding a parameter to you flow. You can read
  more about it in the [prefect docs.](https://docs.prefect.io/core/tutorial/05-running-on-a-schedule.html#running-on-schedule)
