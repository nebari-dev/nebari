from kubernetes import client, config
from zipfile import ZipFile
def create_support_subcommand(subparser):
    subparser = subparser.add_parser("support")


    subparser.set_defaults(func=handle_support)


def handle_support(args):
    config.load_kube_config()

    v1 = client.CoreV1Api()
    # print(dir(v1))
    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    # v1.CustomResourceDefinition
    print(v1.get_api_resources())
    print(v1.get_api_resources_with_http_info())
    # log = v1.read_namespaced_pod_log(watch=False)
    # for i in log.items:
    #     print(i)
    # print(dir(ret.items[0]))
    # for i in ret.items:
    #     print("NEWLINE===================================")
    #     try:
    #         print(v1.read_namespaced_pod_log(name=i.metadata.name, namespace=i.metadata.namespace))
    #         print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name, ))
    #     except client.exceptions.ApiException as e:
    #         print("%s not available"% i.metadata.name)
