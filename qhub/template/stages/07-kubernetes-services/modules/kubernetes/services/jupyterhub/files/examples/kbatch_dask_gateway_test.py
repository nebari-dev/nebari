"""
Start a cluster with Dask Gateway, print the dashboard link, and run some tasks.
"""
import dask
import dask_gateway
import distributed
from distributed import wait


def inc(x):
    return x + 1


def main():
    print(f"dask version         = {dask.__version__}")
    print(f"dask_gateway version = {dask_gateway.__version__}")
    print(f"distributed version  = {distributed.__version__}")

    gateway = dask_gateway.Gateway()
    options = gateway.cluster_options(use_local_defaults=False)

    print("Starting cluster")
    cluster = gateway.new_cluster(options)
    client = cluster.get_client()
    print("Dashboard at:", client.dashboard_link)

    cluster.scale(2)

    futures = client.map(inc, list(range(100)))
    _ = wait(futures)

    print("Closing cluster")
    cluster.close()


if __name__ == "__main__":
    main()
