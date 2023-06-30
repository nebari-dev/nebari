import os

from nebari import schema
from _nebari.stages.bootstrap import CiEnum


def test_render_config(nebari_render):
    output_directory, config_filename = nebari_render
    config = schema.read_configuration(config_filename)
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
    } == set(os.listdir(output_directory / "stages"))

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


# @pytest.fixture
# def write_nebari_config_to_file(setup_fixture, render_config_partial):
#     nebari_config_loc, render_config_inputs = setup_fixture
#     (
#         project,
#         namespace,
#         domain,
#         cloud_provider,
#         ci_provider,
#         auth_provider,
#     ) = render_config_inputs

#     config = render_config_partial(
#         project_name=project,
#         namespace=namespace,
#         nebari_domain=domain,
#         cloud_provider=cloud_provider,
#         ci_provider=ci_provider,
#         auth_provider=auth_provider,
#         kubernetes_version=None,
#     )

#     stages = get_available_stages()
#     render_template(str(nebari_config_loc.parent), config, stages)

#     yield setup_fixture


# def test_render_template(write_nebari_config_to_file):
#     nebari_config_loc, render_config_inputs = write_nebari_config_to_file
#     (
#         project,
#         namespace,
#         domain,
#         cloud_provider,
#         ci_provider,
#         auth_provider,
#     ) = render_config_inputs

#     yaml = YAML()
#     nebari_config_json = yaml.load(nebari_config_loc.read_text())

#     assert nebari_config_json["project_name"] == project
#     assert nebari_config_json["namespace"] == namespace
#     assert nebari_config_json["domain"] == domain
#     assert nebari_config_json["provider"] == cloud_provider


# def test_exists_after_render(write_nebari_config_to_file):
#     items_to_check = [
#         ".gitignore",
#         "stages",
#         "nebari-config.yaml",
#         PRESERVED_DIR,
#     ]

#     nebari_config_loc, _ = write_nebari_config_to_file

#     yaml = YAML()
#     nebari_config_json = yaml.load(nebari_config_loc.read_text())

#     # list of files/dirs available after `nebari render` command
#     ls = os.listdir(Path(nebari_config_loc).parent.resolve())

#     cicd = nebari_config_json.get("ci_cd", {}).get("type", None)

#     if cicd == "github-actions":
#         items_to_check.append(".github")
#     elif cicd == "gitlab-ci":
#         items_to_check.append(".gitlab-ci.yml")

#     for i in items_to_check:
#         assert i in ls
