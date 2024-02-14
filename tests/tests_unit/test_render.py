import os

from nebari.plugins import nebari_plugin_manager


def test_render_config(nebari_render):
    output_directory, config_filename = nebari_render
    config = nebari_plugin_manager.read_config(config_filename)
    assert {"nebari-config.yaml", "stages", ".gitignore"} <= set(
        os.listdir(output_directory)
    )
    assert {
        "07-kubernetes-services",
        "02-infrastructure",
        "01-terraform-state",
        "05-kubernetes-keycloak",
        "08-nebari-tf-extensions",
        "06-kubernetes-keycloak-configuration",
        "04-kubernetes-ingress",
        "03-kubernetes-initialize",
    }.issubset(os.listdir(output_directory / "stages"))

    assert (
        output_directory / "stages" / f"01-terraform-state/{config.provider.value}"
    ).is_dir()
    assert (
        output_directory / "stages" / f"02-infrastructure/{config.provider.value}"
    ).is_dir()
