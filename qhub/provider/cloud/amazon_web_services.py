import json
import subprocess
import functools


@functools.lru_cache()
def regions():
    output = subprocess.check_output(["aws", "ec2", "describe-regions"])
    data = json.loads(output.decode("utf-8"))
    return {_["RegionName"]: _["RegionName"] for _ in data["Regions"]}


@functools.lru_cache()
def zones(region):
    output = subprocess.check_output(
        ["aws", "ec2", "describe-availability-zones", "--region", region]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["ZoneName"]: _["ZoneName"] for _ in data["AvailabilityZones"]}


@functools.lru_cache()
def kubernetes_versions():
    return {_: _ for _ in ["1.13", "1.14", "1.15"]}


@functools.lru_cache()
def instances(region):
    output = subprocess.check_output(
        ["aws", "ec2", "describe-instance-types", "--region", region]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["InstanceType"]: _["InstanceType"] for _ in data["InstanceTypes"]}
