from pathlib import Path
from zipfile import ZipFile

from kubernetes import client, config
from ruamel import yaml

QHUB_SUPPORT_LOG_FILE = "./qhub-support-logs.zip"


def create_support_subcommand(subparser):
    subparser = subparser.add_parser("support")

    subparser.add_argument(
        "-c", "--config", help="qhub configuration yaml file", required=True
    )

    subparser.add_argument(
        "-o", "--output", default=QHUB_SUPPORT_LOG_FILE, help="output filename"
    )

    subparser.set_defaults(func=handle_support)


def handle_support(args):
    config.load_kube_config()

    v1 = client.CoreV1Api()

    namespace = get_config_namespace(config=args.config)

    pods = v1.list_namespaced_pod(namespace=namespace)

    for pod in pods.items:
        Path(f"./log/{namespace}").mkdir(parents=True, exist_ok=True)
        path = Path(f"./log/{namespace}/{pod.metadata.name}.txt")
        with path.open(mode="wt") as file:
            try:
                file.write(
                    "%s\t%s\t%s\n"
                    % (
                        pod.status.pod_ip,
                        namespace,
                        pod.metadata.name,
                    )
                )

                # some pods are running multiple containers
                containers = [
                    _.name if len(pod.spec.containers) > 1 else None
                    for _ in pod.spec.containers
                ]

                for container in containers:
                    if container is not None:
                        file.write(f"Container: {container}\n")
                    file.write(
                        v1.read_namespaced_pod_log(
                            name=pod.metadata.name,
                            namespace=namespace,
                            container=container,
                        )
                    )

            except client.exceptions.ApiException as e:
                file.write("%s not available" % pod.metadata.name)
                raise e

    with ZipFile(QHUB_SUPPORT_LOG_FILE, "w") as zip:
        for file in list(Path(f"./log/{namespace}").glob("*.txt")):
            print(file)
            zip.write(file)


def get_config_namespace(config):
    config_filename = Path(config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    return config["namespace"]
