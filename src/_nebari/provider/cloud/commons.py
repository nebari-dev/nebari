import re

from _nebari.constants import HIGHEST_SUPPORTED_K8S_VERSION


def filter_by_highest_supported_k8s_version(k8s_versions_list):
    filtered_k8s_versions_list = []
    for k8s_version in k8s_versions_list:
        version = tuple(
            filter(None, re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", k8s_version).groups())
        )
        if version <= HIGHEST_SUPPORTED_K8S_VERSION:
            filtered_k8s_versions_list.append(k8s_version)
    return filtered_k8s_versions_list


def filter_amis_by_latest_version(amis_list):
    print(amis_list)
    latest_amis = {}
    for ami in amis_list:
        version = tuple(
            filter(None, re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", ami["Name"]).groups())
        )
        if version not in latest_amis:
            latest_amis[version] = ami.pop("LastModifiedDate")
        else:
            if ami["LastModifiedDate"] > latest_amis[version]["LastModifiedDate"]:
                latest_amis[version] = ami.pop("LastModifiedDate")
    return list(latest_amis.values())
