import json
from pathlib import Path

import typer

from nebari.hookspecs import hookimpl
from _nebari.keycloak import keycloak_rest_api_call


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    app_dev = typer.Typer(
        add_completion=False,
        no_args_is_help=True,
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    cli.add_typer(
        app_dev,
        name="dev",
        help="Development tools and advanced features.",
        rich_help_panel="Additional Commands",
    )

    @app_dev.command(name="keycloak-api")
    def keycloak_api(
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
