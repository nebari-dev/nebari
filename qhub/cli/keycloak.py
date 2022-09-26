import logging
import pathlib

from qhub.keycloak import do_keycloak

# from typing import Tuple


logger = logging.getLogger(__name__)


def create_keycloak_subcommand(subparser):
    subparser = subparser.add_parser("keycloak")
    subparser.add_argument("-c", "--config", help="qhub configuration", required=True)
    subparser.add_argument(
        "keycloak_action",
        nargs="+",
        help="`adduser <username> [password]` or `listusers`",
    )
    subparser.set_defaults(func=handle_keycloak)


def handle_keycloak(args):
    config_filename = pathlib.Path(args.config)
    if not config_filename.is_file():
        raise ValueError(
            f"passed in configuration filename={config_filename} must exist"
        )

    do_keycloak(config_filename, *args.keycloak_action)


# import typer
# from dataclasses import dataclass

# app = typer.Typer()

# @dataclass
# class Common:
#     config: str

# @app.callback()
# def common(ctx: typer.Context,
#     config: str = typer.Option(
#         ...,
#         envvar="APP_CONFIG"
#     )
# ):
#     ctx.obj=Common(
#         config
#     )

# @app.command()
# def add_users(ctx: typer.Context, add_users: Tuple[str, str] = typer.Option(
#         None,
#         "--user",
#         help="`<username> [password]`"
#     )
# ):
#     config_filename = Path(ctx.obj.config)
#     if not config_filename.is_file():
#         raise ValueError(
#             f"passed in configuration filename={config_filename} must exist"
#         )

#     do_keycloak(
#         config_filename,
#         add_user=add_users,
#         listusers=False,
#     )

# @app.command()
# def list_users(ctx: typer.Context):

#     config_filename = Path(ctx.obj.config)
#     if not config_filename.is_file():
#         raise ValueError(
#             f"passed in configuration filename={config_filename} must exist"
#         )

#     do_keycloak(
#         config_filename,
#         add_user=False,
#         listusers=True,
#     )

# if __name__=="__main__":
#     app()
