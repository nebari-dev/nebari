> [!CAUTION]
> **This project has been archived.**
>
> Nebari has had its final release. No further development or releases are planned.
>
> This project has been superseded by [nebari-infrastructure-core (NIC)](https://github.com/nebari-dev/nebari-infrastructure-core), which takes a composable, modular approach to infrastructure management. See the NIC design documents in that repository for the reasoning behind this transition.
>
> Existing Nebari users should refer to the NIC repository for migration guidance.

---

<p align="center">
<picture>
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/nebari-dev/nebari-design/main/logo-mark/horizontal/Nebari-Logo-Horizontal-Lockup.svg">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/nebari-dev/nebari-design/main/logo-mark/horizontal/Nebari-Logo-Horizontal-Lockup-White-text.svg">
  <img alt="Nebari logo mark - text will be black in light color mode and white in dark color mode." src="https://raw.githubusercontent.com/nebari-dev/nebari-design/main/logo-mark/horizontal/Nebari-Logo-Horizontal-Lockup-White-text.svg" width="50%"/>
</picture>
</p>

<h1 align="center"> Your open source data science platform. Built for scale, designed for collaboration. </h1>

---

| Information | Links |
| :---------- | :-----|
|   Project   | [![License](https://img.shields.io/badge/License-BSD%203--Clause-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://opensource.org/licenses/BSD-3-Clause) [![Nebari documentation](https://img.shields.io/badge/%F0%9F%93%96%20Read-the%20docs-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://www.nebari.dev/docs/welcome) [![PyPI](https://img.shields.io/pypi/v/nebari)](https://badge.fury.io/py/nebari) [![conda version](https://img.shields.io/conda/vn/conda-forge/nebari)]((https://anaconda.org/conda-forge/nebari))  |
|  Community  | [![GH discussions](https://img.shields.io/badge/%F0%9F%92%AC%20-Participate%20in%20discussions-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://github.com/nebari-dev/nebari/discussions) [![Open an issue](https://img.shields.io/badge/%F0%9F%93%9D%20Open-an%20issue-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://github.com/nebari-dev/nebari/issues/new/choose) [![Community guidelines](https://img.shields.io/badge/🤝%20Community-guidelines-gray.svg?colorA=2D2A56&colorB=5936D9&style=flat.svg)](https://www.nebari.dev/docs/community/) |

## Nebari

Nebari was an open source data platform for building and maintaining cost-effective, scalable compute platforms on [HPC](https://github.com/nebari-dev/nebari-slurm) or Kubernetes with minimal DevOps overhead.

It used [Terraform](https://www.terraform.io/), [Helm](https://helm.sh/), and [GitHub Actions](https://docs.github.com/en/free-pro-team@latest/actions) to deploy [JupyterHub](https://jupyter.org/hub) with [Dask Gateway](https://docs.dask.org/) on Kubernetes across AWS, GCP, and Azure.

## License

[Nebari is BSD3 licensed](LICENSE).
