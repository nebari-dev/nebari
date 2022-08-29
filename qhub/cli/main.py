import typer

from qhub.cli._init import check_cloud_provider_creds
from qhub.schema import ProviderEnum


def enum_to_list(enum_cls):
    return [e.value for e in enum_cls]


app = typer.Typer(
    help="Nebari CLI 🪴",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command()
def init(
    cloud_provider: str = typer.Argument(
        ...,
        help=f"options: {enum_to_list(ProviderEnum)}",
        callback=check_cloud_provider_creds,
    ),
    project_name: str = typer.Option(
        None,
        "--project-name",
        "--project",
        "-p",
        prompt=True,
    ),
    domain_name: str = typer.Option(
        None,
        "--domain-name",
        "--domain",
        "-d",
        prompt=True,
    ),
    auth_provider: str = typer.Option(
        "password",
        prompt=True,
        # callback=auth_provider_options
    ),
):
    """
    Initialize the nebari-config.yaml file.

    """
    print(f"Cloud provider: {cloud_provider}")
    print(f"Project name: {project_name}")
    print(f"Domain name: {domain_name}")
    print(f"Auth provider: {auth_provider}")


@app.command()
def validate():
    """
    Validate the config.yaml file.

    """
    print("Validate the config.yaml file")


@app.command()
def render():
    """
    Render the config.yaml file.
    """
    print("Render the congig.yaml file")


@app.command()
def deploy():
    """
    Deploy the nebari
    """
    print("Deploy the Nebari")


@app.command()
def destroy():
    """
    Destroy the nebari
    """
    print("Destroy the Nebari")


def main():
    app()


if __name__ == "__main__":
    app()
