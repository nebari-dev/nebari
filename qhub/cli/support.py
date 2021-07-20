from kubernetes import client, config
from pathlib import Path
from zipfile import ZipFile


def create_support_subcommand(subparser):
    subparser = subparser.add_parser("support")

    subparser.add_argument("-f", "--filename", default="./qhub-support.zip", help="output filename")

    subparser.set_defaults(func=handle_support)


def handle_support(args):
    config.load_kube_config()

    v1 = client.CoreV1Api()

    # ret = v1.list_pod_for_all_namespaces(watch=False)
    ret = v1.list_namespaced_pod(namespace='dev')

    for i in ret.items:
        parentDir = Path(f'./log/{i.metadata.namespace}').mkdir(parents=True, exist_ok=True)
        path = Path(f'./log/{i.metadata.namespace}/{i.metadata.name}.txt')
        with path.open(mode='wt') as file:
            try:
                file.write(v1.read_namespaced_pod_log(name=i.metadata.name, namespace=i.metadata.namespace))
                file.write("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name,))
            except client.exceptions.ApiException as e:
                file.write("%s not available"% i.metadata.name)

    with ZipFile('./qhub-support.zip', 'w') as zip:
        for file in list(Path('./log').glob('*.txt')):
            zip.write(file)