import subprocess
import json
import functools


@functools.lru_cache()
def projects():
    output = subprocess.check_output(["gcloud", "projects", "list", "--format=json"])
    data = json.loads(output.decode("utf-8"))
    return {_["name"]: _["projectId"] for _ in data}


@functools.lru_cache()
def regions(project):
    output = subprocess.check_output(
        ["gcloud", "compute", "regions", "list", "--project", project, "--format=json"]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["description"]: _["name"] for _ in data}


@functools.lru_cache()
def zones(project, region):
    output = subprocess.check_output(
        ["gcloud", "compute", "zones", "list", "--project", project, "--format=json"]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["description"]: _["name"] for _ in data if _["name"].startswith(region)}


@functools.lru_cache()
def kubernetes_versions(region):
    output = subprocess.check_output(
        [
            "gcloud",
            "container",
            "get-server-config",
            "--region",
            region,
            "--format=json",
        ]
    )
    data = json.loads(output.decode("utf-8"))
    return {_: _ for _ in data["validMasterVersions"]}


@functools.lru_cache()
def instances(project):
    output = subprocess.check_output(
        [
            "gcloud",
            "compute",
            "machine-types",
            "list",
            "--project",
            project,
            "--format=json",
        ]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["description"]: _["name"] for _ in data}


# Getting pricing data could come from here
# https://cloudpricingcalculator.appspot.com/static/data/pricelist.json
