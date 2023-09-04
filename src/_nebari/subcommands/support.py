import pathlib
from zipfile import ZipFile

import kubernetes.client
import kubernetes.client.exceptions
import kubernetes.config
import typer

from _nebari.config import read_configuration
from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command(rich_help_panel="Additional Commands")
    def support(
        config_filename: pathlib.Path = typer.Option(
            ...,
            "-c",
            "--config",
            help="nebari configuration file path",
        ),
        output: str = typer.Option(
            "./nebari-support-logs.zip",
            "-o",
            "--output",
            help="output filename",
        ),
    ):
        """
        Support tool to write all Kubernetes logs locally and compress them into a zip file.

        The Nebari team recommends k9s to manage and inspect the state of the cluster.
        However, this command occasionally helpful for debugging purposes should the logs need to be shared.
        """
        from nebari.plugins import nebari_plugin_manager

        config_schema = nebari_plugin_manager.config_schema
        namespace = read_configuration(config_filename, config_schema).namespace

        kubernetes.config.kube_config.load_kube_config()

        v1 = kubernetes.client.CoreV1Api()

        pods = v1.list_namespaced_pod(namespace=namespace)

        for pod in pods.items:
            pathlib.Path(f"./log/{namespace}").mkdir(parents=True, exist_ok=True)
            path = pathlib.Path(f"./log/{namespace}/{pod.metadata.name}.txt")
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
                            + "\n"
                        )

                except kubernetes.client.exceptions.ApiException as e:
                    file.write("%s not available" % pod.metadata.name)
                    raise e

        with ZipFile(output, "w") as zip:
            for file in list(pathlib.Path(f"./log/{namespace}").glob("*.txt")):
                print(file)
                zip.write(file)
