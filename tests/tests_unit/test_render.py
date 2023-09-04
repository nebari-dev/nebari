import os

from _nebari.stages.bootstrap import CiEnum
from nebari import schema
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

    if config.provider == schema.ProviderEnum.do:
        assert (output_directory / "stages" / "01-terraform-state/do").is_dir()
        assert (output_directory / "stages" / "02-infrastructure/do").is_dir()
    elif config.provider == schema.ProviderEnum.aws:
        assert (output_directory / "stages" / "01-terraform-state/aws").is_dir()
        assert (output_directory / "stages" / "02-infrastructure/aws").is_dir()
    elif config.provider == schema.ProviderEnum.gcp:
        assert (output_directory / "stages" / "01-terraform-state/gcp").is_dir()
        assert (output_directory / "stages" / "02-infrastructure/gcp").is_dir()
    elif config.provider == schema.ProviderEnum.azure:
        assert (output_directory / "stages" / "01-terraform-state/azure").is_dir()
        assert (output_directory / "stages" / "02-infrastructure/azure").is_dir()

    if config.ci_cd.type == CiEnum.github_actions:
        assert (output_directory / ".github/workflows/").is_dir()
    elif config.ci_cd.type == CiEnum.gitlab_ci:
        assert (output_directory / ".gitlab-ci.yml").is_file()
