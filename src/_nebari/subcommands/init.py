from _nebari.cli.init import (
    check_auth_provider_creds,
    check_cloud_provider_creds,
    check_project_name,
    check_ssl_cert_email,
    enum_to_list,
    guided_init_wizard,
    handle_init,
)


@app.command()
def init(
    cloud_provider: str = typer.Argument(
        "local",
        help=f"options: {enum_to_list(ProviderEnum)}",
        callback=check_cloud_provider_creds,
        is_eager=True,
    ),
    # Although this unused below, the functionality is contained in the callback. Thus,
    # this attribute cannot be removed.
    guided_init: bool = typer.Option(
        False,
        help=GUIDED_INIT_MSG,
        callback=guided_init_wizard,
        is_eager=True,
    ),
    project_name: str = typer.Option(
        ...,
        "--project-name",
        "--project",
        "-p",
        callback=check_project_name,
    ),
    domain_name: str = typer.Option(
        ...,
        "--domain-name",
        "--domain",
        "-d",
    ),
    namespace: str = typer.Option(
        "dev",
    ),
    auth_provider: str = typer.Option(
        "password",
        help=f"options: {enum_to_list(AuthenticationEnum)}",
        callback=check_auth_provider_creds,
    ),
    auth_auto_provision: bool = typer.Option(
        False,
    ),
    repository: str = typer.Option(
        None,
        help=f"options: {enum_to_list(GitRepoEnum)}",
    ),
    repository_auto_provision: bool = typer.Option(
        False,
    ),
    ci_provider: str = typer.Option(
        None,
        help=f"options: {enum_to_list(CiEnum)}",
    ),
    terraform_state: str = typer.Option(
        "remote", help=f"options: {enum_to_list(TerraformStateEnum)}"
    ),
    kubernetes_version: str = typer.Option(
        "latest",
    ),
    ssl_cert_email: str = typer.Option(
        None,
        callback=check_ssl_cert_email,
    ),
    disable_prompt: bool = typer.Option(
        False,
        is_eager=True,
    ),
):
    """
    Create and initialize your [purple]nebari-config.yaml[/purple] file.

    This command will create and initialize your [purple]nebari-config.yaml[/purple] :sparkles:

    This file contains all your Nebari cluster configuration details and,
    is used as input to later commands such as [green]nebari render[/green], [green]nebari deploy[/green], etc.

    If you're new to Nebari, we recommend you use the Guided Init wizard.
    To get started simply run:

            [green]nebari init --guided-init[/green]

    """
    inputs = InitInputs()

    inputs.cloud_provider = cloud_provider
    inputs.project_name = project_name
    inputs.domain_name = domain_name
    inputs.namespace = namespace
    inputs.auth_provider = auth_provider
    inputs.auth_auto_provision = auth_auto_provision
    inputs.repository = repository
    inputs.repository_auto_provision = repository_auto_provision
    inputs.ci_provider = ci_provider
    inputs.terraform_state = terraform_state
    inputs.kubernetes_version = kubernetes_version
    inputs.ssl_cert_email = ssl_cert_email
    inputs.disable_prompt = disable_prompt

    handle_init(inputs)
