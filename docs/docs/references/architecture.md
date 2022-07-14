---
id: source-code-architecture
title: Reference for Nebari source code architecture
---

# Nebari source code architecture

At a high level Nebari has several operations. Each operation has a
corresponding cli file with the same name in
[nebari/cli](https://github.com/Quansight/qhub/blob/main/qhub/cli).

## [nebari/initialize.py](https://github.com/Quansight/qhub/blob/main/qhub/initialize.py)

This operation `initializes` the YAML configuration that is at the
core of Nebari. This YAML file `nebari-config.yaml` schema is declared within
[nebari/schema.py](https://github.com/Quansight/qhub/blob/main/qhub/schema.py). The
schema is the core object that is used as the source of truth and used for validation before the following operations run.

## [nebari/render.py](https://github.com/Quansight/qhub/blob/main/qhub/render.py) 

This operation `renders` the files from the given YAML
configuration. This is a pseudo operation that is never directly
called by the user. It is automatically run with the `deploy`
operation. A `stages` directory is produced.

## [nebari/deploy.py](https://github.com/Quansight/qhub/blob/main/qhub/deploy.py) 

`deploy` infrastructure and kubernetes resources via [Terraform](https://www.terraform.io/)

## [nebari/destroy.py](https://github.com/Quansight/qhub/blob/main/qhub/destroy.py) 

`destroy` infrastructure and kubernetes resources via [Terraform](https://www.terraform.io/). The `destroy` command roughly does the `deploy` command in reverse.

