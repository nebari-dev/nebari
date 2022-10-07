from pathlib import Path
from typing import Tuple

import typer

from qhub.keycloak import do_keycloak

app_keycloak = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app_keycloak.command(name="adduser")
def add_user(
    add_users: Tuple[str, str] = typer.Option(
        ..., "--user", help="Provide both: <username> <password>"
    ),
    config_filename: str = typer.Option(
        ...,
        "-c",
        "--config",
        help="qhub configuration file path",
    ),
):
    """Add a user to Keycloak. User will be automatically added to the [italic]analyst[/italic] group."""
    if isinstance(config_filename, str):
        config_filename = Path(config_filename)

    args = ["adduser", add_users[0], add_users[1]]

    do_keycloak(config_filename, *args)


@app_keycloak.command(name="listusers")
def list_users(
    config_filename: str = typer.Option(
        ...,
        "-c",
        "--config",
        help="qhub configuration file path",
    )
):
    """List the users in Keycloak."""
    if isinstance(config_filename, str):
        config_filename = Path(config_filename)

    args = ["listusers"]

    do_keycloak(config_filename, *args)
