import typer

from _nebari.render import render_template
from _nebari.utils import load_yaml
from nebari import schema
from nebari.hookspecs import hookimpl


@hookimpl
def nebari_subcommand(cli: typer.Typer):
    @cli.command(rich_help_panel="Additional Commands")
    def render(
        output: str = typer.Option(
            "./",
            "-o",
            "--output",
            help="output directory",
        ),
        config: str = typer.Option(
            ...,
            "-c",
            "--config",
            help="nebari configuration yaml file path",
        ),
        dry_run: bool = typer.Option(
            False,
            "--dry-run",
            help="simulate rendering files without actually writing or updating any files",
        ),
    ):
        """
        Dynamically render the Terraform scripts and other files from your [purple]nebari-config.yaml[/purple] file.
        """
        config_filename = Path(config)

        if not config_filename.is_file():
            raise ValueError(
                f"passed in configuration filename={config_filename} must exist"
            )

        config_yaml = load_yaml(config_filename)

        schema.verify(config_yaml)

        render_template(output, config, dry_run=dry_run)
