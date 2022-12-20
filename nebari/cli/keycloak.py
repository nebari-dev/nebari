import json
from pathlib import Path
from typing import Tuple

import typer

from nebari.keycloak import do_keycloak, export_keycloak_users, keycloak_rest_api_call

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
        help="nebari configuration file path",
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
        help="nebari configuration file path",
    )
):
    """List the users in Keycloak."""
    if isinstance(config_filename, str):
        config_filename = Path(config_filename)

    args = ["listusers"]

    do_keycloak(config_filename, *args)


@app_keycloak.command(name="export-users")
def export_users(
    config_filename: str = typer.Option(
        ...,
        "-c",
        "--config",
        help="nebari configuration file path",
    ),
    realm: str = typer.Option(
        "nebari",
        "--realm",
        help="realm from which users are to be exported",
    ),
):
    """Export the users in Keycloak."""
    if isinstance(config_filename, str):
        config_filename = Path(config_filename)

    r = export_keycloak_users(config_filename, realm=realm)

    print(json.dumps(r, indent=4))


@app_keycloak.command(name="rest-api")
def rest_api(
    config_filename: str = typer.Option(
        ...,
        "-c",
        "--config",
        help="nebari configuration file path",
    ),
    request: str = typer.Option(
        ...,
        "-r",
        "--request",
        help="Send a REST API request, valid requests follow patterns found here: [green]keycloak.org/docs-api/15.0/rest-api[/green]",
    ),
):
    """
    Interact with the Keycloak REST API directly.

    This is an advanced tool which can have potentially destructive consequences.
    Please use this at your own risk.

    """
    if isinstance(config_filename, str):
        config_filename = Path(config_filename)

    r = keycloak_rest_api_call(config_filename, request=request)

    print(json.dumps(r, indent=4))
