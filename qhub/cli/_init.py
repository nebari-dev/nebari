import os

import typer

from qhub.schema import ProviderEnum


def check_cloud_provider_creds(cloud_provider: str):

    cloud_provider = cloud_provider.lower()

    if cloud_provider == ProviderEnum.aws.value and (
        not os.environ.get("AWS_ACCESS_KEY_ID")
        or not os.environ.get("AWS_SECRET_ACCESS_KEY")
    ):
        print(
            "\nUnable to location AWS credentials, please generate your AWS keys at this link: aws.com/..."
        )
        os.environ["AWS_ACCESS_KEY_ID"] = typer.prompt(
            "Please enter your AWS_ACCESS_KEY_ID",
            hide_input=True,
        )
        os.environ["AWS_SECRET_ACCESS_KEY"] = typer.prompt(
            "Please enter your AWS_SECRET_ACCESS_KEY",
            hide_input=True,
        )

    elif cloud_provider == ProviderEnum.gcp.value and (
        not os.environ.get("GOOGLE_CREDENTIALS") or not os.environ.get("PROJECT_ID")
    ):
        print(
            "\nUnable to location AWS credentials,please generate your GCP credentials at this link: [link=https://cloud.google.com/iam/docs/creating-managing-service-accounts][/link]"
        )
        os.environ["GOOGLE_CREDENTIALS"] = typer.prompt(
            "Please enter your GOOGLE_CREDENTIALS",
            hide_input=True,
        )
        os.environ["PROJECT_ID"] = typer.prompt(
            "Please enter your PROJECT_ID",
            hide_input=True,
        )

    elif cloud_provider == ProviderEnum.do.value and (
        not os.environ.get("DIGITALOCEAN_TOKEN")
        or not os.environ.get("SPACES_ACCESS_KEY_ID")
        or not os.environ.get("SPACES_SECRET_ACCESS_KEY")
        or not os.environ.get("AWS_ACCESS_KEY_ID")
        or not os.environ.get("AWS_SECRET_ACCESS_KEY")
    ):
        print(
            "\nUnable to location AWS credentials, please generate your Digital Ocean token at this link: [link=https://docs.digitalocean.com/reference/api/create-personal-access-token/][/link]"
        )
        os.environ["DIGITALOCEAN_TOKEN"] = typer.prompt(
            "Please enter your DIGITALOCEAN_TOKEN",
            hide_input=True,
        )
        os.environ["SPACES_ACCESS_KEY_ID"] = typer.prompt(
            "Please enter your SPACES_ACCESS_KEY_ID",
        )
        os.environ["SPACES_SECRET_ACCESS_KEY"] = typer.prompt(
            "Please enter your SPACES_SECRET_ACCESS_KEY",
            hide_input=True,
        )
        os.environ["AWS_ACCESS_KEY_ID"] = typer.prompt(
            "Please set this variable with the same value as `AWS_ACCESS_KEY_ID`",
            hide_input=True,
        )
        os.environ["AWS_SECRET_ACCESS_KEY"] = typer.prompt(
            "Please set this variable with the same value as `AWS_SECRET_ACCESS_KEY`",
            hide_input=True,
        )

    elif (
        cloud_provider == "AZURE"
        and not os.environ.get("ARM_CLIENT_ID")
        and not os.environ.get("ARM_CLIENT_SECRET")
        and not os.environ.get("ARM_SUBSCRIPTION_ID")
        and not os.environ.get("ARM_TENANT_ID")
    ):
        print(
            "Please generate your AWS keys at this link: [link=https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/guides/service_principal_client_secret#creating-a-service-principal-in-the-azure-portal][/link]"
        )
        os.environ["ARM_CLIENT_ID"] = typer.prompt(
            "Please enter your ARM_CLIENT_ID",
            hide_input=True,
        )
        os.environ["ARM_CLIENT_SECRET"] = typer.prompt(
            "Please enter your ARM_CLIENT_SECRET",
            hide_input=True,
        )
        os.environ["ARM_SUBSCRIPTION_ID"] = typer.prompt(
            "Please enter your ARM_SUBSCRIPTION_ID",
            hide_input=True,
        )
        os.environ["ARM_TENANT_ID"] = typer.prompt(
            "Please enter your ARM_TENANT_ID",
            hide_input=True,
        )


# testing questionary package
# def auth_provider_options(auth_provider):
#     import questionary

#     if auth_provider == None:
#         auth_provider = questionary.select(
#             "auth provider ...",
#             choices=["password", "github", "auth0"],
#         ).ask()

#     return auth_provider
