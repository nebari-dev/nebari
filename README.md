# QHub-Ops

Is tool for initializing and maintaining the state of QHub deployments

## Installation:

```bash
python setup.py install
```

## Initializing the Provider Template

* Amazon Web Services

```bash
qhub_ops render -c tests/assets/config_aws.yaml
```

* Digital Ocean

```bash
qhub-ops render -c tests/assets/config_do.yaml -f
```

* Google Cloud Platform

```bash
qhub-ops render -c tests/assets/config_gcp.yaml
```

After initialising the provider templates, follow the instructions
in docs: `qhub-ops/qhub_ops/template/{{ cookiecutter.project_name }}/docs/`

## Terraform Module Dependencies

This project depends on the terraform modules repository:
https://github.com/Quansight/qhub-terraform-modules

# License

qhub-ops is BSD3 licensed


