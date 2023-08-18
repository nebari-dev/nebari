import functools
import os

import boto3

from _nebari import constants
from _nebari.provider.cloud.commons import filter_by_highest_supported_k8s_version


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


@functools.lru_cache()
def regions():
    client = boto3.client("ec2")
    response = client.describe_regions()
    return {_["RegionName"]: _["RegionName"] for _ in response["Regions"]}


@functools.lru_cache()
def zones():
    client = boto3.client("ec2")
    response = client.describe_availability_zones()
    return {_["ZoneName"]: _["ZoneName"] for _ in response["AvailabilityZones"]}


@functools.lru_cache()
def kubernetes_versions():
    """Return list of available kubernetes supported by cloud provider. Sorted from oldest to latest."""
    # AWS SDK (boto3) currently doesn't offer an intuitive way to list available kubernetes version. This implementation grabs kubernetes versions for specific EKS addons. It will therefore always be (at the very least) a subset of all kubernetes versions still supported by AWS.

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
def instances():
    client = boto3.client("ec2")
    paginator = client.get_paginator('describe_instance_types')
    instance_types = sorted([ j["InstanceType"] for i in paginator.paginate() for j in i["InstanceTypes"] ])
    return {t: t for t in instance_types}
