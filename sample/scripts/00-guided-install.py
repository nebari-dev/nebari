from subprocess import check_output
from shutil import which
from os import path, environ
import os

SUPPORTED_VERSIONS = ["v0.13"]

# 01 Verify configuration file exists
if not path.exists("qhub-ops-config.yaml"):
    raise Exception('Configuration file "qhub-ops-config.yaml" does not exist')

# 02 Check if Terraform works
if which("terraform") is None:
    raise Exception(
        f"Please install Terraform with one of the following minor releases: {SUPPORTED_VERSIONS}"
    )

# 03 Check version of Terraform
if (
    check_output(["terraform", "--version"]).decode("utf-8")[10:15]
    not in SUPPORTED_VERSIONS
):
    raise Exception(
        f"Unsupported Terraform version. Supported minor releases: {SUPPORTED_VERSIONS}"
    )

# 04 Check Environment Variables

do_env_docs = "https://qhub.readthedocs.io/en/latest/docs/do/installation.html#environment-variables"
required_variables = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "SPACES_ACCESS_KEY_ID",
    "SPACES_SECRET_ACCESS_KEY",
    "DIGITALOCEAN_TOKEN"
]

missing_variables = [_ for _ in required_variables if _ not in environ]

if len(missing_variables) > 0:
    raise Exception(f"""Missing the following required environment variables: {required_variables}
\n
Please see the documentation for more information: {do_env_docs}
    """)
    
if environ["AWS_ACCESS_KEY_ID"] != environ["SPACES_ACCESS_KEY_ID"]:
    raise Exception(f"""The environment variables AWS_ACCESS_KEY_ID and SPACES_ACCESS_KEY_ID must equal each other. 
    \n
See {do_env_docs} for more information""")
    
if environ["AWS_SECRET_ACCESS_KEY"] != environ["SPACES_SECRET_ACCESS_KEY"]:
    raise Exception(f"""The environment variables AWS_SECRET_ACCESS_KEY and SPACES_SECRET_ACCESS_KEY must equal each other. 
    \n
See {do_env_docs} for more information""")



# 05 Check that oauth settings are set
input("Ensure that oauth settings are in configuration [Press \"Enter\" to continue]")

# 06 Create terraform backend remote state bucket
os.chdir("terraform-state")
os.system("terraform init")
os.system("terraform apply -auto-approve")

# 07 Create qhub initial state (up to nginx-ingress)
os.chdir("../infrastructure")
os.system("terraform init")
os.system("terraform apply -auto-approve -target=module.kubernetes -target=module.kubernetes-initialization -target=module.kubernetes-ingress")

# 08 Update DNS to point to qhub deployment
input(f"Take IP Address Above and update DNS to point to \"jupyter.do_script.qhub.dev\" [Press Enter when Complete]")

# 09 Full deploy QHub
os.system("terraform apply -auto-approve")
