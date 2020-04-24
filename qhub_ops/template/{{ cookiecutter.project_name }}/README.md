# {{ cookiecutter.repo_name }} Infrastructure

This guide is intended to show how to deploy and maintain a jupyterhub
cluster along with its related components. Infastructure as code is
used, via GitHub Actions and Terraform, such that this repository will
always reflect the exact state of the cluster. Advantages of this
infrastructure as code approach:

 - reduce the requirements for developers on their machines
 - restrict modifications to infrastructure
 - enable review of infastructure changes
 - allow arbitrary users to request infrastructure changes

In practice GitHub Actions controls everything.

## Dependencies

 - [awscli](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)
 - [aws-iam-authenticator](https://docs.aws.amazon.com/eks/latest/userguide/install-aws-iam-authenticator.html)
 - [doctl](https://github.com/digitalocean/doctl#installing-doctl)
 - [gcloud](https://cloud.google.com/sdk/install)
 - [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
 - [helm](https://helm.sh/) version **3+**
 - [terraform](https://www.terraform.io/downloads.html)

## Development

Adding `terraform-state` and `infastructure`

## Deployment


