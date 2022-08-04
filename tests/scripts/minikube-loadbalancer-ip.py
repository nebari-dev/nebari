#!/usr/bin/env python
import json
import os
import subprocess
import sys

minikube_cmd = ["minikube", "ssh", "--", "ip", "-j", "a"]
minikube_output = subprocess.check_output(minikube_cmd, encoding="utf-8")[:-1]

address = None
for interface in json.loads(minikube_output):
    if interface["ifname"] == "eth0":
        address = interface["addr_info"][0]["local"].split(".")
        break
else:
    print("minikube interface eth0 not found")
    sys.exit(1)

filename = os.path.expanduser("~/.minikube/profiles/minikube/config.json")
with open(filename) as f:
    data = json.load(f)

start_address, end_address = ".".join(address[0:3] + ["100"]), ".".join(
    address[0:3] + ["150"]
)
print("Setting start=%s end=%s" % (start_address, end_address))
data["KubernetesConfig"]["LoadBalancerStartIP"] = start_address
data["KubernetesConfig"]["LoadBalancerEndIP"] = end_address

with open(filename, "w") as f:
    json.dump(data, f)
