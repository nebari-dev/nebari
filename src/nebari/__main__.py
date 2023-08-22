import typer

from _nebari.cli import create_cli


def main():
    cli = create_cli()
    cli()


# get the click object from the typer app so that we can autodoc the cli
# NOTE: this must happen _after_ all the subcommands have been added.
# Adapted from https://typer.tiangolo.com/tutorial/using-click/
typer_click_app = typer.main.get_command(create_cli())

if __name__ == "__main__":
    typer_click_app()
