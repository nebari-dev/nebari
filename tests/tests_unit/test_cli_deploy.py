def test_dns_option(config_gcp, runner, cli):
    result = runner.invoke(
        cli,
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
