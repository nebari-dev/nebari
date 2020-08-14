import subprocess
import json
import functools


@functools.lru_cache()
def instances():
    output = subprocess.check_output(
        ["doctl", "kubernetes", "options", "sizes", "-o=json"]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["name"]: _["slug"] for _ in data}


@functools.lru_cache()
def regions():
    output = subprocess.check_output(
        ["doctl", "kubernetes", "options", "regions", "-o=json"]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["name"]: _["slug"] for _ in data}


@functools.lru_cache()
def kubernetes_versions():
    output = subprocess.check_output(
        ["doctl", "kubernetes", "options", "versions", "-o=json"]
    )
    data = json.loads(output.decode("utf-8"))
    return {_["kubernetes_version"]: _["slug"] for _ in data}
