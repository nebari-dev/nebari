import json
import pathlib
from typing import Tuple

import typer

from _nebari.config import read_configuration
from _nebari.keycloak import do_keycloak, export_keycloak_users
from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    app_keycloak = typer.Typer(
        add_completion=False,
        no_args_is_help=True,
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    cli.add_typer(
        app_keycloak,
        name="keycloak",
        help="Interact with the Nebari Keycloak identity and access management tool.",
        rich_help_panel="Additional Commands",
    )

    @app_keycloak.command(name="adduser")
    def add_user(
        add_users: Tuple[str, str] = typer.Option(
            ..., "--user", help="Provide both: <username> <password>"
        ),
        config_filename: pathlib.Path = typer.Option(
            ...,
            "-c",
            "--config",
            help="nebari configuration file path",
        ),
    ):
        """Add a user to Keycloak. User will be automatically added to the [italic]analyst[/italic] group."""
        from nebari.plugins import nebari_plugin_manager

        args = ["adduser", add_users[0], add_users[1]]
        config_schema = nebari_plugin_manager.config_schema
        config = read_configuration(config_filename, config_schema)
        do_keycloak(config, *args)

    @app_keycloak.command(name="listusers")
    def list_users(
        config_filename: pathlib.Path = typer.Option(
            ...,
            "-c",
            "--config",
            help="nebari configuration file path",
        )
    ):
        """List the users in Keycloak."""
        from nebari.plugins import nebari_plugin_manager

        args = ["listusers"]
        config_schema = nebari_plugin_manager.config_schema
        config = read_configuration(config_filename, config_schema)
        do_keycloak(config, *args)

    @app_keycloak.command(name="export-users")
    def export_users(
        config_filename: pathlib.Path = typer.Option(
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
        from nebari.plugins import nebari_plugin_manager

        config_schema = nebari_plugin_manager.config_schema
        config = read_configuration(config_filename, config_schema=config_schema)
        r = export_keycloak_users(config, realm=realm)
        print(json.dumps(r, indent=4))
