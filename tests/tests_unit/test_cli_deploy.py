from typer.testing import CliRunner

from _nebari.cli import create_cli

runner = CliRunner()


def test_dns_option(config_gcp):
    app = create_cli()
    result = runner.invoke(
        app,
        [
            "deploy",
            "-c",
            str(config_gcp),
            "--dns-provider",
            "cloudflare",
            "--dns-auto-provision",
        ],
    )
    assert (
        "The `--dns-provider` and `--dns-auto-provision` flags have been removed"
        in result.output
    )
    assert "Aborted" in result.output
