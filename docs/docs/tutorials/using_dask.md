---
id: using_dask
title: Working with big data using Dask
description: Introduction to Dask
---

# Working with big data using Dask

Working with large datasets can pose a few challenges, running into frequent memory issues is a common issue. 
[Dask](https://docs.dask.org/en/stable/) is a free and open-source library for parallel computing in Python,
enabling data scientist and others to use their favorite PyData tools at scale.

## Dask integration on Nebari

Nebari uses [Dask Gateway](https://gateway.dask.org/) to expose auto-scaling compute clusters automatically 
configured for the user, and provides a secure way to managing dask clusters. 

<details>
<summary> Want more information on how that works? </summary>

Dask consists of 3 main components `client`, `scheduler` and `workers`.
- The end users interact with the `client`. 
- The `scheduler` tracks metrics and coordinate workers.
- The `workers` are the threads/processes that executes computations.

The `client` interacts with both `scheduler` (sends instructions) and `workers` (collects results)

Check out the [Dask Gateway documentation](https://gateway.dask.org/) for a full explanation.

</details>

## Setting up Dask Gateway

We will start by creating a Jupyter notebook. Select an environment from the `Select kernel` dropdown menu 
(located on the top right of your notebook). Be sure to select an environment which incudes `Dask`!

Nebari has set of pre-defined options for configuring the Dask profiles that we have access to. These can be 
accessed via Dask Gateway options.

```python
from dask_gateway import Gateway
# instantiate dask gateway
gateway = Gateway()

# view the cluster options UI
options = gateway.cluster_options()
options
```

![Cluster Options UI](/img/cluster_options.png)

Using the `Cluster Options` interface, we can specify the conda environment, the instance type, and any additional 
environment variables we'll need. 

:::warning
It’s important that the environment used for your notebook matches the Dask worker environment!

The Dask worker environment is specified in your deployment directory under `/image/dask-worker/environment.yaml`
:::

## Creating a Dask cluster

```python
# create a new cluster with our options
cluster = gateway.new_cluster(options)
# view the cluster UI
cluster
```

![Creating a Gateway Cluster UI](/img/cluster_creation.png)

We have the option to choose between `Manual Scaling` and `Adaptive Scaling`.

If you know the resources that would be required for the computation, you can select `Manual Scaling` and 
define a number of workers to spin up. These will remain in the cluster until it is shut down. 

Alternatively, if you aren't sure how many workers you'll need, or if parts of your workflow require more workers
than others, you can select `Adaptive Scaling`. Dask Gateway will automatically scale the number of workers
(spinning up new workers or shutting down unused ones) depending on the computational burder. `Adaptive Scaling` is
a safe way to prevent running out of memory, while not burning excess resources. 

You may also notice a link to the Dask Dashboard in this interface. We'll discuss this in a later section. 

## Viewing the Dask Client

```python
# get the client for the cluster
client = cluster.get_client()
# view the client UI
client
```

![dask client ui](/img/dask_client.png)

The `Dask Client` interface gives us a brief summary of everything we've set up so far. 

## Now for the fun part - let's code with Dask! 

```python
import dask.array as da
x = da.random.random((100000, 100000), chunks=(1000, 1000))
y = x * x
z = y.mean(axis=1)
z.compute()
```

**Sample output: Dask compute**
```shell
array([0.33349882, 0.33262234, 0.33379292, ..., 0.33177493, 0.33396109,
       0.33385578])
```

In the above code snippet, we are first generating a random array of shape (10000*10000), which is a large array.
In order to fit it into our memory we specify the argument `chunks` which breaks the underlying array into
chunks. Here we are using uniform dimension `1000`, meaning chunks of 1000 in each dimension. Storing it in variable
`x`. Further some simple computations are performed, and finally we compute the column wise mean operation 
on the array `z`.

![variable x](/img/x_array.png)    ![variable z](/img/z_array.png) 

### Dask diagnostic UI

Dask comes with an inbuilt dashboard containing multiple plots and tables containing live information as 
the data gets processed. Let's understand the dashboard plots `Task Stream` and `Progress`. 
The colours and the interpretation would differ based on the computation we choose.

Each of the computation in split into multiple tasks for parallel execution. From the progress bar we see 04
distinct colours associated with different computation. Under task stream (a streaming plot) each row represents a thread
and the small rectangles within are the individual tasks. The tiny white spaces shows that the worker was ideal during 
that period of time.

![dask diagnostic UI](/img/dask_diagostic_UI.png)

### Shutting down the cluster

As you you may have noticed, its easy to spin up a lot of compute, really quickly. 

**With Great Power Comes Great Responsibility**

**ALWAYS** remember to shutdown your cluster!! *Resources cost something!!* 

```python
cluster.close(shutdown=True)
```


## Viewing the dashboard inside of JupyterLab

[Dask-labextension](https://github.com/dask/dask-labextension) provides a JupyterLab extension to manage Dask clusters,
as well as embed Dask's dashboard plots directly into JupyterLab panes.
Nebari includes this extension by default, elevating the overall developer experience.

![Dask-labextension ui](/img/dask_labextension.png)


## Using Dask safely

If you're anything like us, we've forgotten to shut down our cluster a time or two. Wrapping the dask-gateway in a 
context manager is a great practice that ensures the cluster is fully shutdown once the task is complete! 

### Sample Dask `context manager` configuration

We like to use something like this context manager to help us manager our clusters. It can be written once and 
included in your codebase. The one we've included here includes some default setup options. You can write your 
own to adjust to your needs. 

```python
import os
import time
import dask.array as da
from contextlib import contextmanager

import dask
from distributed import Client
from dask_gateway import Gateway

@contextmanager
def dask_cluster(n_workers=2, worker_type="Small Worker", conda_env="filesystem/dask"):
    try:
        gateway = Gateway()
        options = gateway.cluster_options()
        options.conda_environment = conda_env
        options.profile = worker_type
        print(f"Gateway: {gateway}")
        for key, value in options.items():
            print(f"{key} : {value}")

        cluster = gateway.new_cluster(options)
        client = Client(cluster)
        if os.getenv("JUPYTERHUB_SERVICE_PREFIX"):
            print(cluster.dashboard_link)

        cluster.scale(n_workers)
        client.wait_for_workers(1)

        yield client

    finally:
        cluster.close()
        client.close()
        del client
        del cluster
```

Now we can write our compute tasks inside of the context manager and all of the setup and teardown
is managed for us! 

```python
with dask_cluster() as client:
    x = da.random.random((10000, 10000), chunks=(1000, 1000))
    y = x + x.T
    z = y[::2, 5000:].mean(axis=1)
    result = z.compute()
    print(client.run(os.getpid))
```

:::

## Conclusion

Kudos ✨, we now have a working Dask cluster inside Nebari.  
Now go load up your own big data!
