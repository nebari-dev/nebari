import typer

from nebari.hookspecs import hookimpl


def get_config_namespace(config):
    config_filename = Path(config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    with config_filename.open() as f:
        config = yaml.safe_load(f.read())

    return config["namespace"]


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command(rich_help_panel="Additional Commands")
    def support(
        config_filename: str = typer.Option(
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
        kube_config.load_kube_config()

        v1 = client.CoreV1Api()

        namespace = get_config_namespace(config=config_filename)

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

        with ZipFile(output, "w") as zip:
            for file in list(Path(f"./log/{namespace}").glob("*.txt")):
                print(file)
                zip.write(file)
