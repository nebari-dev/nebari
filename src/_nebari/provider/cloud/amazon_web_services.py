import functools
import json
import os
import subprocess
import time

import boto3
from botocore.exceptions import ClientError

from _nebari import constants
from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version

MAX_RETRIES = 5
DELAY = 5


def check_credentials():
    for variable in {
        "AWS_DEFAULT_REGION",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
    }:
        if variable not in os.environ:
            raise ValueError(
                f"""Missing the following required environment variable: {variable}\n
                Please see the documentation for more information: {constants.AWS_ENV_DOCS}"""
            )


def aws_session(region: str = "nyc3", digitalocean: bool = False):
    # TODO: determine a cleaner way of handling region
    if digitalocean:
        aws_access_key_id = os.environ["SPACES_ACCESS_KEY_ID"]
        aws_secret_access_key = os.environ["SPACES_SECRET_ACCESS_KEY"]
    else:
        check_credentials()
        aws_access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
        aws_secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
        region = os.environ["AWS_DEFAULT_REGION"]

    return boto3.Session(
        region_name=region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )


@functools.lru_cache()
def regions():
    session = aws_session()
    ec2_client = session.client("ec2")
    regions = ec2_client.describe_regions()["Regions"]
    return {_["RegionName"]: _["RegionName"] for _ in regions}


@functools.lru_cache()
def zones(region: str = "us-west-2"):
    output = subprocess.check_output(
        ["aws", "ec2", "describe-availability-zones", "--region", region]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["ZoneName"]: _["ZoneName"] for _ in data["AvailabilityZones"]}


@functools.lru_cache()
def kubernetes_versions(region="us-west-2"):
    """Return list of available kubernetes supported by cloud provider. Sorted from oldest to latest."""
    # AWS SDK (boto3) currently doesn't offer an intuitive way to list available kubernetes version. This implementation grabs kubernetes versions for specific EKS addons. It will therefore always be (at the very least) a subset of all kubernetes versions still supported by AWS.
    if not os.getenv("AWS_DEFAULT_REGION"):
        os.environ["AWS_DEFAULT_REGION"] = region

    client = boto3.client("eks")
    supported_kubernetes_versions = list()
    available_addons = client.describe_addon_versions()
    for addon in available_addons.get("addons", None):
        for eksbuild in addon.get("addonVersions", None):
            for k8sversion in eksbuild.get("compatibilities", None):
                supported_kubernetes_versions.append(
                    k8sversion.get("clusterVersion", None)
                )

    supported_kubernetes_versions = sorted(list(set(supported_kubernetes_versions)))
    return filter_by_highest_supported_k8s_version(supported_kubernetes_versions)


@functools.lru_cache()
def instances(region: str = "us-west-2"):
    output = subprocess.check_output(
        ["aws", "ec2", "describe-instance-types", "--region", region]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["InstanceType"]: _["InstanceType"] for _ in data["InstanceTypes"]}


def aws_delete_s3_bucket(
    bucket_name: str,
    region: str,
    endpoint: str = None,
    digitalocean: bool = False,
):
    session = aws_session(region=region, digitalocean=digitalocean)
    s3 = session.resource("s3", endpoint_url=endpoint)
    try:
        bucket = s3.Bucket(bucket_name)

        for obj in bucket.objects.all():
            obj.delete()

        for obj_version in bucket.object_versions.all():
            obj_version.delete()

    except ClientError as e:
        if "NoSuchBucket" in str(e):
            print(f"Bucket {bucket_name} does not exist. Skipping...")
            return
        else:
            raise e

    for i in range(MAX_RETRIES):
        try:
            bucket.delete()
            print(f"Successfully deleted bucket {bucket_name}")
            return
        except ClientError as e:
            if "BucketNotEmpty" in str(e):
                print(f"Bucket is not yet empty. Retrying in {DELAY} seconds...")
                time.sleep(DELAY)
            else:
                raise e
    print(f"Failed to delete bucket {bucket_name} after {MAX_RETRIES} retries.")


def aws_delete_node_groups(cluster_name: str, region: str):
    session = aws_session(region=region)
    eks = session.client("eks")
    node_groups = eks.list_nodegroups(clusterName=cluster_name)["nodegroups"]
    print(node_groups)

    for node_group in node_groups:
        try:
            eks.delete_nodegroup(clusterName=cluster_name, nodegroupName=node_group)
            print(
                f"Initiated deletion for node group {node_group} belonging to cluster {cluster_name}"
            )
        except ClientError as e:
            if "ResourceNotFoundException" not in str(e):
                raise e

    retries = 0
    while retries < MAX_RETRIES:
        pending_deletion = []

        for node_group in node_groups:
            try:
                response = eks.describe_nodegroup(
                    clusterName=cluster_name, nodegroupName=node_group
                )
                if response["nodegroup"]["status"] == "DELETING":
                    pending_deletion.append(node_group)
            except ClientError as e:
                if "ResourceNotFoundException" in str(e):
                    pass
                else:
                    raise e

        if not pending_deletion:
            print("All node groups have been deleted successfully.")
            return

        if retries < MAX_RETRIES - 1:
            sleep_time = DELAY * (2**retries)
            print(
                f"{len(pending_deletion)} node groups still pending deletion. Retrying in {sleep_time} seconds..."
            )
            time.sleep(sleep_time)
            retries += 1

    print(f"Failed to confirm deletion of all node groups after {MAX_RETRIES} retries.")


def aws_delete_cluster(cluster_name: str, region: str):
    session = aws_session(region=region)
    eks = session.client("eks")

    try:
        eks.delete_cluster(name=cluster_name)
        print(f"Initiated deletion for cluster {cluster_name}")
    except ClientError as e:
        if "ResourceNotFoundException" in str(e):
            print(f"Cluster {cluster_name} not found. Exiting...")
            return
        else:
            raise e

    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = eks.describe_cluster(name=cluster_name)
            if response["cluster"]["status"] == "DELETING":
                sleep_time = DELAY * (2**retries)
                print(
                    f"Cluster {cluster_name} still pending deletion. Retrying in {sleep_time} seconds..."
                )
                time.sleep(sleep_time)
                retries += 1
            else:
                raise ClientError(
                    f"Unexpected status for cluster {cluster_name}: {response['cluster']['status']}"
                )
        except ClientError as e:
            if "ResourceNotFoundException" in str(e):
                print(f"Cluster {cluster_name} has been deleted successfully.")
                return
            else:
                raise e

    print(
        f"Failed to confirm deletion of cluster {cluster_name} after {MAX_RETRIES} retries."
    )


def aws_cleanup(name: str, namespace: str, region: str):
    # TODO: complete cleanup steps
    cluster_name = f"{name}-{namespace}"

    aws_delete_node_groups(cluster_name, region)
    aws_delete_cluster(cluster_name, region)
