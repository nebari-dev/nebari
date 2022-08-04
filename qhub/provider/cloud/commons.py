from qhub.constants import HIGHEST_SUPPORTED_K8S_VERSION


def filter_by_highest_supported_k8s_version(k8s_versions_list):
    filtered_k8s_versions_list = []
    for k8s_version in k8s_versions_list:
        if k8s_version <= HIGHEST_SUPPORTED_K8S_VERSION:
            filtered_k8s_versions_list.append(k8s_version)
    return filtered_k8s_versions_list
