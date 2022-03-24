# Changelog

> Contains description of QHub releases.

______________________________________________________________________

## Upcoming Release

### Feature changes and enhancements

### Bug fixes

## Release v0.4.0 - March 17, 2022

Version `v0.4.0` introduced many design changes along with a handful of user-facing changes that require some justification. Unfortunately as a result of these changes, QHub
instance that are upgraded from previous version to `v0.4.0` will irrevocably break.

Until we have a fully functioning backup mechanism, anyone looking to upgrade is highly encouraged to backup their data, see the
[upgrade docs](https://docs.qhub.dev/en/latest/source/admin_guide/breaking-upgrade.html) and more specifically, the
[backup docs](https://docs.qhub.dev/en/latest/source/admin_guide/backup.html).

The design changes that we are referring to were considered important enough that the developers felt they were warranted. Below we try to highlight a few of the largest changes
and provide justification for them.

- Replace Terraforms resource targeting with staged Terraform deployments.
  - *Justification*: using Terraform resource targeting was never an ideal way of handing off outputs from stage to the next and Terraform explicitly warns its users that it's only
    intended to be used "is provided only for exceptional situations such as recovering from errors or mistakes".
- Fully remove `cookiecutter` as a templating mechanism.
  - *Justification*: Although `cookiecutter` has its benefits, we were becoming overly reliant on it as a means to many various scripts needed for deployment. Reading through
    Terraform scripts with scattered `cookiecutter` statements was increasing troublesome and a bit intimidating. Our IDEs are also much happier about this change.
- Removing users and groups from the `qhub-config.yaml` and replacing user management with Keycloak.
  - *Justification*: Up until now, any change to QHub deployment needed to be made in the `qhub-config.yaml` which had the benefit of centralizing any configuration. However it
    also potentially limited the kinds of user management tasks while also causing the `qhub-config.yaml` to balloon in size. Another benefit of removing users and groups from the
    `qhub-config.yaml` are that deserves highlighting is that user management no longer requires a full redeployment.

Although breaking changes are never fun, we hope the reasons outlined above are encouraging signs that we are working on building a better, more stable yet flexible product. If you
experience any issues or have any questions about these changes, feel free to open an [issue on our Github repo](https://github.com/Quansight/qhub/issues).

## Breaking changes

Explicit user facing changes:

- Upgrading to `v0.4.0` will require a filesystem backup given the scope and size of the current change set.
  - Running `qhub upgrade` will produce an updated `qhub-config.yaml` and a JSON file of users that can then be imported into Keycloak.
- With the addition of Keycloak, QHub will no longer support `security.authentication.type = custom`.
  - No more users and groups in the `qhub-config.yaml`.

## Feature changes and enhancements

- Authentication is now managed by Keycloak.
- QHub Helm extension mechanism added.
- Allow JupyterHub overrides in the `qhub-config.yaml`.
- `qhub support` CLI option to save Kubernetes logs.
- Updates `conda-store` UI.

## What's Changed

<details>

- Enabling Vale CI with GitHub Actions by @HarshCasper in https://github.com/Quansight/qhub/pull/871
- Qhub upgrade by @danlester in https://github.com/Quansight/qhub/pull/870
- Documentation cleanup by @HarshCasper in https://github.com/Quansight/qhub/pull/873
- \[Docs\] Add Traefik wildcard docs by @viniciusdc in https://github.com/Quansight/qhub/pull/876
- replace deprecated "minikube cache add" with "minikube image load" by @Adam-D-Lewis in https://github.com/Quansight/qhub/pull/880
- Azure Python needs different env var names to Terraform by @danlester in https://github.com/Quansight/qhub/pull/882
- Add notes about broken upgrades by @tylerpotts in https://github.com/Quansight/qhub/pull/877
- Keycloak integration first pass by @danlester in https://github.com/Quansight/qhub/pull/848
- K8s tests - keycloak adduser by @danlester in https://github.com/Quansight/qhub/pull/890
- Documentation cleanup by @HarshCasper in https://github.com/Quansight/qhub/pull/889
- Improvements to templates and readme by @trallard in https://github.com/Quansight/qhub/pull/893
- Keycloak docs by @danlester in https://github.com/Quansight/qhub/pull/901
- DOCS: Add a PR Template by @HarshCasper in https://github.com/Quansight/qhub/pull/900
- Delete existing `.gitlab-ci.yml` when rendering by @iameskild in https://github.com/Quansight/qhub/pull/887
- Qhub Extension (Ready for Review) by @Adam-D-Lewis in https://github.com/Quansight/qhub/pull/886
- Updates to Readme by @trallard in https://github.com/Quansight/qhub/pull/897
- Mirror docker images to ghcr and quay container registry by @aktech in https://github.com/Quansight/qhub/pull/912
- Fix CI: skip failure on cleanup by @aktech in https://github.com/Quansight/qhub/pull/910
- Create and solve envs using mamba by @iameskild in https://github.com/Quansight/qhub/pull/915
- Pin terraform providers by @Adam-D-Lewis in https://github.com/Quansight/qhub/pull/914
- qhub-config.yaml as a secret by @danlester in https://github.com/Quansight/qhub/pull/905
- Setup/Add integration/deployment tests via pytest by @aktech in https://github.com/Quansight/qhub/pull/922
- Disabl/Remove the stale bot by @viniciusdc in https://github.com/Quansight/qhub/pull/923
- Integrates Hadolint for Dockerfile linting by @HarshCasper in https://github.com/Quansight/qhub/pull/917
- Reduce minimum nodes in user and dask node pools to 0 for Azure / GCP by @tarundmsharma in https://github.com/Quansight/qhub/pull/723
- Allow jupyterhub.overrides in qhub-config.yaml by @danlester in https://github.com/Quansight/qhub/pull/930
- qhub destroy using targets by @danlester in https://github.com/Quansight/qhub/pull/948
- Take AWS region from AWS_DEFAULT_REGION into qhub-config.yaml on init… by @danlester in https://github.com/Quansight/qhub/pull/950
- cookicutter template out of raw by @danlester in https://github.com/Quansight/qhub/pull/951
- kubernetes-initialization depends_on kubernetes by @danlester in https://github.com/Quansight/qhub/pull/952
- Add timeout to terraform import command by @tylerpotts in https://github.com/Quansight/qhub/pull/949
- Timeout in process (for import) by @danlester in https://github.com/Quansight/qhub/pull/955
- Remove user/groups from YAML by @danlester in https://github.com/Quansight/qhub/pull/956
- qhub upgrade custom auth plus tests by @danlester in https://github.com/Quansight/qhub/pull/946
- Add minimal support `centos` images by @iameskild in https://github.com/Quansight/qhub/pull/943
- Keycloak Export by @danlester in https://github.com/Quansight/qhub/pull/947
- qhub cli tool to save kubernetes logs - `qhub support` by @tarundmsharma in https://github.com/Quansight/qhub/pull/818
- Add docs for deploying QHub to existing EKS cluster by @iameskild in https://github.com/Quansight/qhub/pull/944
- Add jupyterhub-idle-culler to jupyterhub image by @danlester in https://github.com/Quansight/qhub/pull/959
- Robust external container registry by @danlester in https://github.com/Quansight/qhub/pull/945
- use qhub-jupyterhub-theme 0.3.3 to simplify JupyterHub config by @danlester in https://github.com/Quansight/qhub/pull/966
- Get kubernetes version for all cloud providers + pytest refactor by @iameskild in https://github.com/Quansight/qhub/pull/927
- Merge hub.extraEnv env vars by @danlester in https://github.com/Quansight/qhub/pull/968
- DOCS: Removing errors from documentation by @HarshCasper in https://github.com/Quansight/qhub/pull/941
- keycloak.realm_display_name by @danlester in https://github.com/Quansight/qhub/pull/973
- minor updates to keycloak docs by @tylerpotts in https://github.com/Quansight/qhub/pull/977
- CI changes for QHub by @HarshCasper in https://github.com/Quansight/qhub/pull/989
- Update `upgrade` docs and general doc improvements by @iameskild in https://github.com/Quansight/qhub/pull/990
- Remove `scope`, `oauth_callback_url` during upgrade step by @iameskild in https://github.com/Quansight/qhub/pull/997
- Adding Conda-Store to QHub by @costrouc in https://github.com/Quansight/qhub/pull/967
- Fix Jupyterlab docker build by @viniciusdc in https://github.com/Quansight/qhub/pull/1001
- DOCS: Fix broken link in setup doc by @HarshCasper in https://github.com/Quansight/qhub/pull/1006
- Fix Kubernetes local test deployment by @viniciusdc in https://github.com/Quansight/qhub/pull/1002
- Initial commit for auth and stages workflow by @costrouc in https://github.com/Quansight/qhub/pull/1003
- Fix formatting issues with black #1003 by @viniciusdc in https://github.com/Quansight/qhub/pull/1020
- use pyproject.toml and setup.cfg for packaging by @tonyfast in https://github.com/Quansight/qhub/pull/986
- Increase timeout/attempts for keycloak check by @viniciusdc in https://github.com/Quansight/qhub/pull/1023
- Fix issue with traefik issuing certificates with let's encrypt acme by @costrouc in https://github.com/Quansight/qhub/pull/1017
- Fixing cds dashboard conda environments being shown by @costrouc in https://github.com/Quansight/qhub/pull/1025
- Fix input variable support for multiple types by @viniciusdc in https://github.com/Quansight/qhub/pull/1029
- Fix Black/Flake8 problems by @danlester in https://github.com/Quansight/qhub/pull/1039
- Add remote state condition for 01-terraform-state provisioning by @viniciusdc in https://github.com/Quansight/qhub/pull/1042
- Round versions for upgrade and schema by @danlester in https://github.com/Quansight/qhub/pull/1038
- Code Server is now installed via conda, and the Jupyterlab Extension is https://github.com/betatim/vscode-binder/ by @costrouc in https://github.com/Quansight/qhub/pull/1044
- Removing cookiecutter from setup.cfg requirements by @costrouc in https://github.com/Quansight/qhub/pull/1026
- Destroy terraform-state stage when condition match by @viniciusdc in https://github.com/Quansight/qhub/pull/1051
- Fix up adding support for security.keycloak.realm_display_name key by @costrouc in https://github.com/Quansight/qhub/pull/1054
- Move external_container_reg to earlier stage by @danlester in https://github.com/Quansight/qhub/pull/1053
- Adding ability to specify overrides back into keycloak configuration by @costrouc in https://github.com/Quansight/qhub/pull/1055
- Deprecating terraform_modules option since no longer used by @costrouc in https://github.com/Quansight/qhub/pull/1057
- Adding security.shared_users_group option for default users group by @costrouc in https://github.com/Quansight/qhub/pull/1056
- Fix up adding back jupyterhub overrides option by @costrouc in https://github.com/Quansight/qhub/pull/1058
- prevent_deploy flag for safeguarding upgrades by @danlester in https://github.com/Quansight/qhub/pull/1047
- CI: Add layer caching for Docker images by @HarshCasper in https://github.com/Quansight/qhub/pull/1061
- Additions to TCP/DNS stage check, fix 1027 by @iameskild in https://github.com/Quansight/qhub/pull/1063
- FIX: Remove concurrency groups by @HarshCasper in https://github.com/Quansight/qhub/pull/1064
- Stage 08 extensions and realms/logout by @danlester in https://github.com/Quansight/qhub/pull/1069
- Auto create/destroy azure resource group by @viniciusdc in https://github.com/Quansight/qhub/pull/1071
- Add CICD schema and render workflows by @iameskild in https://github.com/Quansight/qhub/pull/1068
- Ensure that the shared folder symlink only exists if user has shared folders by @costrouc in https://github.com/Quansight/qhub/pull/1074
- Adds the ability on render to deleted targeted files or directories by @costrouc in https://github.com/Quansight/qhub/pull/1073
- DOCS: QHub 101 by @HarshCasper in https://github.com/Quansight/qhub/pull/1011
- remove jovyan user by @tylerpotts in https://github.com/Quansight/qhub/pull/1089
- More finely scoped github actions and kubernetes_test build docker images by @costrouc in https://github.com/Quansight/qhub/pull/1088
- Adding clearml overrides by @costrouc in https://github.com/Quansight/qhub/pull/1059
- Reorganizing render, deploy, destroy to unify stages input_vars, tf_objects, checks, and state_imports by @costrouc in https://github.com/Quansight/qhub/pull/1091
- Updates/fixes for rendering CICD workflows by @iameskild in https://github.com/Quansight/qhub/pull/1086
- fix bug in state_01_terraform_state function call by @tylerpotts in https://github.com/Quansight/qhub/pull/1094
- Use paths instead of paths-ignore so that test only run on changes to given paths by @costrouc in https://github.com/Quansight/qhub/pull/1097
- \[ENH\] - Update issue templates by @trallard in https://github.com/Quansight/qhub/pull/1083
- Generate independent objects for terraform-state resources by @viniciusdc in https://github.com/Quansight/qhub/pull/1102
- Complete implementation of destroy which goes through each stage by @costrouc in https://github.com/Quansight/qhub/pull/1103
- Change AWS Kubernetes provider authentication to use data.eks_cluster instead of exec by @costrouc in https://github.com/Quansight/qhub/pull/1107
- Relax qhub destroy to attempt to continue destroying resources by @costrouc in https://github.com/Quansight/qhub/pull/1109
- Breaking upgrade docs (0.4) by @danlester in https://github.com/Quansight/qhub/pull/1087
- Simplify default images by @tylerpotts in https://github.com/Quansight/qhub/pull/1114
- Change group structure by @danlester in https://github.com/Quansight/qhub/pull/1112
- Adding status field to each destroy stage to print status by @costrouc in https://github.com/Quansight/qhub/pull/1116
- Incorrect mapping of values to gcp node group instance types by @costrouc in https://github.com/Quansight/qhub/pull/1117
- FIX: Remove Conda Store from default images by @HarshCasper in https://github.com/Quansight/qhub/pull/1119
- Minor fix to `setup.cfg` by @iameskild in https://github.com/Quansight/qhub/pull/1122
- \[DOC\]- Update contribution guidelines by @trallard in https://github.com/Quansight/qhub/pull/1080
- Adding tests to visit additional endpoints by @costrouc in https://github.com/Quansight/qhub/pull/1118
- Adding tests for juypterhub-ssh, jhub-client, and vs code by @costrouc in https://github.com/Quansight/qhub/pull/1123
- Update Keycloak docs by @iameskild in https://github.com/Quansight/qhub/pull/1093
- Upgrade conda-store v0.3.10 and simplify specification of image by @HarshCasper in https://github.com/Quansight/qhub/pull/1130
- \[ImgBot\] Optimize images by @imgbot in https://github.com/Quansight/qhub/pull/1140
- Adjust Idle culler settings and add internal culling by @viniciusdc in https://github.com/Quansight/qhub/pull/1133
- \[BUG\] Removing jovyan home directory and issue with nss configuration by @costrouc in https://github.com/Quansight/qhub/pull/1142
- \[DOC\] Add `troubleshooting` docs by @iameskild in https://github.com/Quansight/qhub/pull/1139
- Update user login guides by @viniciusdc in https://github.com/Quansight/qhub/pull/1144
- \[ImgBot\] Optimize images by @imgbot in https://github.com/Quansight/qhub/pull/1146
- Workaround for kubernetes-client version issue by @iameskild in https://github.com/Quansight/qhub/pull/1148
- Make the commit of the terraform rendering optional (replaces PR 995) by @iameskild in https://github.com/Quansight/qhub/pull/1149
- Fix typos in user guide docs by @ericdatakelly in https://github.com/Quansight/qhub/pull/1154
- Minor docs clean up for v0.4.0 release by @iameskild in https://github.com/Quansight/qhub/pull/1155
- Read-the-docs and documentation updates by @tonyfast in https://github.com/Quansight/qhub/pull/1153
- Add markdown formatter for doc wrapping by @viniciusdc in https://github.com/Quansight/qhub/pull/1152
- remove deprecated param `count` from `.cirun.yml` by @aktech in https://github.com/Quansight/qhub/pull/1164
- Use qhub-bot for keycloak deployment/check by @iameskild in https://github.com/Quansight/qhub/pull/1167
- Only list active conda-envs for dask-gateway by @iameskild in https://github.com/Quansight/qhub/pull/1162

</details>

## New Contributors

- @imgbot made their first contribution in https://github.com/Quansight/qhub/pull/1140
- @ericdatakelly made their first contribution in https://github.com/Quansight/qhub/pull/1154

**Full Changelog**: https://github.com/Quansight/qhub/compare/v0.3.13...v0.4.0

## Release 0.3.13 - October 13, 2021

### Breaking changes

- No known breaking changes

### Feature changes and enhancements

- Allow users to specify external Container Registry ([#741](https://github.com/Quansight/qhub/pull/741))
- Integrate Prometheus and Grafana into QHub ([#733](https://github.com/Quansight/qhub/pull/733))
- Add Traefik Dashboard ([#797](https://github.com/Quansight/qhub/pull/797))
- Make ForwardAuth optional for ClearML ([#830](https://github.com/Quansight/qhub/pull/830))
- Include override configuration for Prefect Agent ([#813](https://github.com/Quansight/qhub/pull/813))
- Improve authentication type checking ([#834](https://github.com/Quansight/qhub/pull/834))
- Switch to pydata Sphinx theme ([#805](https://github.com/Quansight/qhub/pull/805))

### Bug fixes

- Add force-destroy command (only for AWS at the moment) ([#694](https://github.com/Quansight/qhub/pull/694))
- Include namespace in conda-store PVC ([#716](https://github.com/Quansight/qhub/pull/716))
- Secure ClearML behind ForwardAuth ([#721](https://github.com/Quansight/qhub/pull/721))
- Fix connectivity issues with AWS EKS via Terraform ([#734](https://github.com/Quansight/qhub/pull/734))
- Fix conda-store pod eviction and volume conflicts ([#740](https://github.com/Quansight/qhub/pull/740))
- Update `remove_existing_renders` to only delete QHub related files/directories ([#800](https://github.com/Quansight/qhub/pull/800))
- Reduce number of AWS subnets down to 4 to increase the number of available nodes by a factor of 4 ([#839](https://github.com/Quansight/qhub/pull/839))

## Release 0.3.11 - May 7, 2021

### Breaking changes

### Feature changes and enhancements

- better validation messages on github auto provisioning

### Bug fixes

- removing default values from pydantic schema which caused invalid yaml files to unexpectedly pass validation
- make kubespawner_override.environment overridable (prior changes were overwritten)

## Release 0.3.10 - May 6,2021

### Breaking changes

- reverting `qhub_user` default name to `jovyan`

### Feature changes and enhancements

### Bug fixes

## Release 0.3.9 - May 5, 2021

### Breaking changes

### Feature changes and enhancements

### Bug fixes

- terraform formatting in cookiecutter for enabling GPUs on GCP

## Release 0.3.8 - May 5, 2021

### Breaking changes

### Feature changes and enhancements

- creating releases for QHub simplified
- added an image for overriding the dask-gateway being used

### Bug fixes

- dask-gateway exposed by default now properly
- typo in cookiecutter for enabling GPUs on GCP

## Release 0.3.7 - April 30, 2021

### Breaking changes

### Feature changes and enhancements

- setting `/bin/bash` as the default terminal

### Bug fixes

- `jhsingle-native-proxy` added to the base jupyterlab image

## Release 0.3.6 - April 29, 2021

### Breaking changes

- simplified bash jupyterlab image to no longer have dashboard packages panel, etc.

### Feature changes and enhancements

- added emacs and vim as default editors in image
- added jupyterlab-git and jupyterlab-sidecar since they now support 3.0
- improvements with `qhub destroy` cleanly deleting resources
- allow user to select conda environments for dashboards
- added command line argument `--skip-terraform-state-provision` to allow for skipping terraform state provisioning in `qhub deploy` step
- no longer render `qhub init` `qhub-config.yaml` file in alphabetical order
- allow user to select instance sizes for dashboards

### Bug fixes

- fixed gitlab-ci before_script and after_script
- fixed jovyan -> qhub_user home directory path issue with dashboards

## Release 0.3.5 - April 28, 2021

### Breaking changes

### Feature changes and enhancements

- added a `--skip-remote-state-provision` flag to allow `qhub deploy` within CI to skip the remote state creation
- added saner defaults for instance sizes and jupyterlab/dask profiles
- `qhub init` no longer renders `qhub-config.yaml` in alphabetical order
- `spawn_default_options` to False to force dashboard owner to pick profile
- adding `before_script` and `after_script` key to `ci_cd` to allow customization of CI process

### Bug fixes

## Release 0.3.4 - April 27, 2021

### Breaking changes

### Feature changes and enhancements

### Bug fixes

- remaining issues with ci_cd branch not being fully changed

## Release 0.3.3 - April 27, 2021

### Breaking changes

### Feature changes and enhancements

### Bug fixes

- Moved to ruamel as yaml parser to throw errors on duplicate keys
- fixed a url link error in cds dashboards
- Azure fixes to enable multiple deployments under one account
- Terraform formatting issue in acme_server deployment
- Terraform errors are caught by qhub and return error code

### Breaking changes

## Release 0.3.2 - April 20, 2021

### Bug fixes

- prevent gitlab-ci from freezing on gitlab deployment
- not all branches were configured via the `branch` option in `ci_cd`

## Release 0.3.1 - April 20, 2021

### Feature changes an enhancements

- added gitlab support for CI
- `ci_cd` field is now optional
- AWS provider now respects the region set
- More robust errors messages in cli around project name and namespace
- `git init` default branch is now `main`
- branch for CI/CD is now configurable

### Bug fixes

- typo in `authenticator_class` for custom authentication

## Release 0.3.0 - April 14, 2021

### Feature changes and enhancements

- Support for self-signed certificate/secret keys via kubernetes secrets
- [jupyterhub-ssh](https://github.com/yuvipanda/jupyterhub-ssh) (`ssh` and `sftp` integration) accessible on port `8022` and `8023` respectively
- VSCode([code-server](https://github.com/cdr/code-server)) now provided in default image and integrated with jupyterlab
- [Dask Gateway](https://gateway.dask.org/) now accessible outside of cluster
- Moving fully towards traefik as a load balancer with tight integration with dask-gateway
- Adding ability to specify node selector label for general, user, and worker
- Ability to specify `kube_context` for local deployments otherwise will use default
- Strict schema validation for `qhub-config.yaml`
- Terraform binary is auto-installed and version managed by qhub
- Deploy stage will auto render by default removing the need for render command for end users
- Support for namespaces with qhub deployments on kubernetes clusters
- Full JupyterHub theming including colors now.
- JupyterHub docker image now independent from zero-to-jupyterhub.
- JupyterLab 3 now default user Docker image.
- Implemented the option to locally deploy QHub allowing for local testing.
- Removed the requirement for DNS, authorization is now password-based (no more OAuth requirements).
- Added option for password-based authentication
- CI now tests local deployment on each commit/PR.
- QHub Terraform modules are now pinned to specific git branch via `terraform_modules.repository` and `terraform_modules.ref`.
- Adds support for Azure cloud provider.

### Bug fixes

### Breaking changes

- Terraform version is now pinned to specific version
- `domain` attributed in `qhub-config.yaml` is now the url for the cluster

### Migration guide

0. Version `<version>` is in format `X.Y.Z`
1. Create release branch `release-<version>` based off `main`
2. Ensure full functionality of QHub this involves at a minimum ensuring

- \[ \] GCP, AWS, DO, and local deployment
- \[ \] "Let's Encrypt" successfully provisioned
- \[ \] Dask Gateway functions properly on each
- \[ \] JupyterLab functions properly on each

3. Increment the version number in `qhub/VERSION` in format `X.Y.Z`
4. Ensure that the version number in `qhub/VERSION` is used in pinning QHub in the github actions `qhub/template/{{ cookiecutter.repo_directory }}/.github/workflows/qhub-ops.yaml`
   in format `X.Y.Z`
5. Create a git tag pointing to the release branch once fully tested and version numbers are incremented `v<version>`

______________________________________________________________________

## Release 0.2.3 - February 5, 2021

### Feature changes, and enhancements

- Added conda prerequisites for GUI packages.
- Added `qhub destroy` functionality that tears down the QHub deployment.
- Changed the default repository branch from `master` to `main`.
- Added error message when Terraform parsing fails.
- Added templates for GitHub issues.

### Bug fixes

- `qhub deploy -c qhub-config.yaml` no longer prompts unsupported argument for `load_config_file`.
- Minor changes on the Step-by-Step walkthrough on the docs.
- Revamp of README.md to make it concise and highlight QHub HPC.

### Breaking changes

- Removed the registry for DigitalOcean.

## Thank you for your contributions!

> [Brian Larsen](https://github.com/brl0), [Rajat Goyal](https://github.com/RajatGoyal), [Prasun Anand](https://github.com/prasunanand), and
> [Rich Signell](https://github.com/rsignell-usgs) and [Josef Kellndorfer](https://github.com/jkellndorfer) for the insightful discussions.
