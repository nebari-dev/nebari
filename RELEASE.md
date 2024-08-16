# Release notes

*Contains description of Nebari releases.*

<!-- Note:
The RELEASE.md file at the root of the Nebari codebase is the source of truth for all release notes.
If you want to update the release notes, open a PR against nebari-dev/nebari.
This file is copied to nebari-dev/nebari-docs using a GitHub Action. -->

---

### Release 2024.7.1 - August 8, 2024

> NOTE: Support for Digital Ocean deployments using CLI commands and related Terraform modules is being deprecated. Although Digital Ocean will no longer be directly supported in future releases, you can still deploy to Digital Ocean infrastructure using the current `existing` deployment option.

## What's Changed
* Enable authentication by default in jupyter-server by @krassowski in https://github.com/nebari-dev/nebari/pull/2288
* remove dns sleep by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2550
* Conda-store permissions v2 + load roles from keycloak by @aktech in https://github.com/nebari-dev/nebari/pull/2531
* Restrict public access and add bucket encryption using cmk by @dcmcand in https://github.com/nebari-dev/nebari/pull/2525
* Add overwrite to AWS coredns addon by @dcmcand in https://github.com/nebari-dev/nebari/pull/2538
* Add a default roles at initialisation by @aktech in https://github.com/nebari-dev/nebari/pull/2546
* Hide gallery section if no exhibits are configured by @krassowski in https://github.com/nebari-dev/nebari/pull/2549
* Add note about ~/.bash_profile by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2575
* Expose jupyterlab-gallery branch and depth options by @krassowski in https://github.com/nebari-dev/nebari/pull/2556
* #2566 Upgrade Jupyterhub ssh image by @arjxn-py in https://github.com/nebari-dev/nebari/pull/2576
* Stop copying unnecessary files into user home directory by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2578
* Include deprecation notes for init/deploy subcommands by @viniciusdc in https://github.com/nebari-dev/nebari/pull/2582
* Only download jar if file doesn't exist by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2588
* Remove unnecessary experimental flag by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2606
* Add typos spell checker to pre-commit by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2568
* Enh 2451 skip conditionals by @BrianCashProf in https://github.com/nebari-dev/nebari/pull/2569
* Improve codespell support: adjust and concentrate config to pyproject.toml and fix more typos by @yarikoptic in https://github.com/nebari-dev/nebari/pull/2583
* Move codespell config to pyproject.toml only by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2611
* Add `depends_on` for bucket encryption by @viniciusdc in https://github.com/nebari-dev/nebari/pull/2615

## New Contributors
* @BrianCashProf made their first contribution in https://github.com/nebari-dev/nebari/pull/2569
* @yarikoptic made their first contribution in https://github.com/nebari-dev/nebari/pull/2583


**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2024.6.1...2024.7.1


### Release 2024.6.1 - June 26, 2024

> NOTE: This release includes an upgrade to the `kube-prometheus-stack` Helm chart, resulting in a newer version of Grafana. When upgrading your Nebari cluster, you will be prompted to have Nebari update some CRDs and delete a DaemonSet on your behalf. If you prefer, you can also run the commands yourself, which will be shown to you. If you have any custom dashboards, you'll also need to back them up by [exporting them as JSON](https://grafana.com/docs/grafana/latest/dashboards/share-dashboards-panels/#export-a-dashboard-as-json), so you can [import them](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/import-dashboards/#import-a-dashboard) after upgrading.

### What's Changed
* Fetch JupyterHub roles from Keycloak by @krassowski in https://github.com/nebari-dev/nebari/pull/2447
* Update selector for Start server button to use button tag by @krassowski in https://github.com/nebari-dev/nebari/pull/2464
* Reduce GCP Fixed Costs by 50% by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2453
* Restore JupyterHub updates from PR-2427 by @viniciusdc in https://github.com/nebari-dev/nebari/pull/2465
* Workload identity by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2460
* Fix test using a non-specific selector by @krassowski in https://github.com/nebari-dev/nebari/pull/2475
* add verify=false since we use self signed cert in tests by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2481
* fix forward auth when using custom cert by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2479
* Upgrade to JupyterHub 5.0.0b2 by @krassowski in https://github.com/nebari-dev/nebari/pull/2468
* upgrade instructions for PR 2453 by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2466
* Use Helm Chart for JupyterHub 5.0.0 final by @krassowski in https://github.com/nebari-dev/nebari/pull/2484
* Parse and insert keycloak roles scopes into JupyterHub by @aktech in https://github.com/nebari-dev/nebari/pull/2471
* Add CITATION file by @pavithraes in https://github.com/nebari-dev/nebari/pull/2455
* CI: add azure integration by @fangchenli in https://github.com/nebari-dev/nebari/pull/2061
* Create trivy.yml by @dcmcand in https://github.com/nebari-dev/nebari/pull/2458
* don't run azure deployment on PRs, only on schedule and manual trigger by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2498
* add cloud provider deployment status badges to README.md by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2407
* Upgrade kube-prometheus-stack helm chart by @marcelovilla in https://github.com/nebari-dev/nebari/pull/2472
* upgrade note by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2502
* Remove VSCode from jhub_apps default services by @jbouder in https://github.com/nebari-dev/nebari/pull/2503
* Explicit config by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2294
* fix general node scaling bug for azure by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2517
* Skip running cleanup on pull requests by @aktech in https://github.com/nebari-dev/nebari/pull/2488
* 1792 Add docstrings to `upgrade.py` by @arjxn-py in https://github.com/nebari-dev/nebari/pull/2512
* set's min TLS version for azure storage account to TLS 1.2 by @dcmcand in https://github.com/nebari-dev/nebari/pull/2522
* Fix conda-store and Traefik Grafana Dashboards by @marcelovilla in https://github.com/nebari-dev/nebari/pull/2540
* Implement support for jupyterlab-gallery config by @krassowski in https://github.com/nebari-dev/nebari/pull/2501
* Add option to run CRDs updates and DaemonSet deletion on user's behalf. by @marcelovilla in https://github.com/nebari-dev/nebari/pull/2544

### New Contributors
* @arjxn-py made their first contribution in https://github.com/nebari-dev/nebari/pull/2512

**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2024.5.1...2024.6.1

### Release 2024.5.1 - May 13, 2024

## What's Changed

* make userscheduler run on general node group by @Adam-D-Lewis in <https://github.com/nebari-dev/nebari/pull/2415>
* Upgrade to Pydantic V2 by @Adam-D-Lewis in <https://github.com/nebari-dev/nebari/pull/2348>
* Pydantic2 PR fix by @Adam-D-Lewis in <https://github.com/nebari-dev/nebari/pull/2421>
* remove redundant pydantic class, fix bug by @Adam-D-Lewis in <https://github.com/nebari-dev/nebari/pull/2426>
* Update `python-keycloak` version pins constraints by @viniciusdc in <https://github.com/nebari-dev/nebari/pull/2435>
* add HERA_TOKEN env var to user pods by @Adam-D-Lewis in <https://github.com/nebari-dev/nebari/pull/2438>
* fix docs link by @Adam-D-Lewis in <https://github.com/nebari-dev/nebari/pull/2443>
* Update allowed admin groups by @aktech in <https://github.com/nebari-dev/nebari/pull/2429>

**Full Changelog**: <https://github.com/nebari-dev/nebari/compare/2024.4.1...2024.5.1>

## Release 2024.4.1 - April 20, 2024

### What's Changed
* update azurerm version by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2370
* Get JupyterHub `groups` from Keycloak, support `oauthenticator` 16.3+ by @krassowski in https://github.com/nebari-dev/nebari/pull/2361
* add full names for cloud providers in guided init by @exitflynn in https://github.com/nebari-dev/nebari/pull/2375
* Add middleware to prefix JupyterHub navbar items with /hub. by @marcelovilla in https://github.com/nebari-dev/nebari/pull/2360
* CLN: split #1928, refactor render test by @fangchenli in https://github.com/nebari-dev/nebari/pull/2246
* add trailing slash for jupyterhub proxy paths by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2387
* remove references to deprecated cdsdashboards by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2390
* add default node groups to config by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2398
* Update concurrency settings for Integration tests by @viniciusdc in https://github.com/nebari-dev/nebari/pull/2393
* Make CI/CD Cloud Provider Test Conditional by @tylergraff in https://github.com/nebari-dev/nebari/pull/2369

### New Contributors
* @exitflynn made their first contribution in https://github.com/nebari-dev/nebari/pull/2375

**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2024.3.3...2024.4.1


## Release 2024.3.3 - March 27, 2024

### What's Changed
* get default variable value when following a terraform variable by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2322
* Upgrade Actions versions by @isumitjha in https://github.com/nebari-dev/nebari/pull/2291
* Cleanup spawner logs by @krassowski in https://github.com/nebari-dev/nebari/pull/2328
* Fix loki gateway url when deployed on non-dev namespace by @aktech in https://github.com/nebari-dev/nebari/pull/2327
* Dmcandrew update ruamel.yaml by @dcmcand in https://github.com/nebari-dev/nebari/pull/2315
* upgrade auth0-python version to ultimately resolve CVE-2024-26130 by @tylergraff in https://github.com/nebari-dev/nebari/pull/2314
* remove deprecated code paths by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2349
* Create SECURITY.md by @dcmcand in https://github.com/nebari-dev/nebari/pull/2354
* Set node affinity for more pods to ensure they run on general node pool by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2353
* Deduplicate conda-store in JupyterLab main menu by @krassowski in https://github.com/nebari-dev/nebari/pull/2347
* Pass current namespace to argo via environment variable by @krassowski in https://github.com/nebari-dev/nebari/pull/2317
* PVC for Traefik Ingress (prevent LetsEncrypt throttling) by @kenafoster in https://github.com/nebari-dev/nebari/pull/2352

### New Contributors
* @isumitjha made their first contribution in https://github.com/nebari-dev/nebari/pull/2291
* @tylergraff made their first contribution in https://github.com/nebari-dev/nebari/pull/2314

**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2024.3.2...2024.3.3

## Release 2024.3.2 - March 14, 2024

### What's Changed
* update max k8s versions and remove depreciated api usage in local deploy by @dcmcand in https://github.com/nebari-dev/nebari/pull/2276
* update keycloak image repo by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2312
* Generate random password for Grafana by @aktech in https://github.com/nebari-dev/nebari/pull/2289
* update conda store to 2024.3.1 by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/2316
* Switch PyPI release workflow to use trusted publishing by @viniciusdc in https://github.com/nebari-dev/nebari/pull/2323


**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2024.3.1...2024.3.2

## Release 2024.3.1 - March 11, 2024

### What's Changed
* Modify Playwright test to account for changes in JupyterLab UI. by @marcelovilla in https://github.com/nebari-dev/nebari/pull/2232
* Add favicon to jupyterhub theme. by @jbouder in https://github.com/nebari-dev/nebari/pull/2222
* Set min nodes to 0 for worker and user. by @pt247 in https://github.com/nebari-dev/nebari/pull/2168
* Remove `jhub-client` from pyproject.toml by @pavithraes in https://github.com/nebari-dev/nebari/pull/2242
* Include permission validation step to programmatically cloned repos by @viniciusdc in https://github.com/nebari-dev/nebari/pull/2258
* Expose jupyter's preferred dir as a config option by @krassowski in https://github.com/nebari-dev/nebari/pull/2251
* Allow to configure default settings for JupyterLab (`overrides.json`) by @krassowski in https://github.com/nebari-dev/nebari/pull/2249
* Feature/jlab menu customization by @marcelovilla in https://github.com/nebari-dev/nebari/pull/2259
* Add cloud provider to the dask config.json file by @marcelovilla in https://github.com/nebari-dev/nebari/pull/2266
* Fix syntax error in jupyter-server-config Python file by @krassowski in https://github.com/nebari-dev/nebari/pull/2286
* Add "Open VS Code" entry in services by @krassowski in https://github.com/nebari-dev/nebari/pull/2267
* Add Grafana Loki integration by @aktech in https://github.com/nebari-dev/nebari/pull/2156

### New Contributors
* @jbouder made their first contribution in https://github.com/nebari-dev/nebari/pull/2222
* @krassowski made their first contribution in https://github.com/nebari-dev/nebari/pull/2251

**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2024.1.1...2024.3.1


## Release 2024.1.1 - January 17, 2024

### Feature changes and enhancements

* Upgrade conda-store to latest version 2024.1.1
* Add Jhub-Apps
* Add Jupyterlab-pioneer
* Minor improvements and bug fixes

### Breaking Changes

> WARNING: jupyterlab-videochat, retrolab, jupyter-tensorboard, jupyterlab-conda-store and jupyter-nvdashboard are no longer supported in Nebari version and will be uninstalled."

### What's Changed

* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/2176
* Fix logic for dns lookup. by @pt247 in https://github.com/nebari-dev/nebari/pull/2166
* Integrate JupyterHub App Launcher into Nebari by @aktech in https://github.com/nebari-dev/nebari/pull/2185
* Pass in permissions boundary to k8s module by @aktech in https://github.com/nebari-dev/nebari/pull/2153
* Add jupyterlab-pioneer by @aktech in https://github.com/nebari-dev/nebari/pull/2127
* JHub Apps: Filter conda envs by user by @aktech in https://github.com/nebari-dev/nebari/pull/2187
* update upgrade command by @dcmcand in https://github.com/nebari-dev/nebari/pull/2198
* Remove JupyterLab from services list by @aktech in https://github.com/nebari-dev/nebari/pull/2189
* Adding fields to ignore within keycloak_realm by @costrouc in https://github.com/nebari-dev/nebari/pull/2200
* Add Nebari menu item configuration. by @marcelovilla in https://github.com/nebari-dev/nebari/pull/2196
* Disable "Newer update available" popup as default setting by @viniciusdc in https://github.com/nebari-dev/nebari/pull/2192
* Block usage of pip inside jupyterlab  by @viniciusdc in https://github.com/nebari-dev/nebari/pull/2191
* Return all environments instead of just those under the user's namespace for jhub-apps by @marcelovilla in https://github.com/nebari-dev/nebari/pull/2206
* Adding a temporary writable directory for conda-store server /home/conda by @costrouc in https://github.com/nebari-dev/nebari/pull/2209
* Add demo repositories mechanism to populate user's space by @viniciusdc in https://github.com/nebari-dev/nebari/pull/2207
* update nebari_workflow_controller and conda_store tags to test rc by @dcmcand in https://github.com/nebari-dev/nebari/pull/2210
* 2023.12.1 release notes by @dcmcand in https://github.com/nebari-dev/nebari/pull/2211
* Make it so that jhub-apps default theme doesn't override by @costrouc in https://github.com/nebari-dev/nebari/pull/2213
* Adding additional theme variables to jupyterhub theme config by @costrouc in https://github.com/nebari-dev/nebari/pull/2215
* updates Current Release to 2024.1.1 by @dcmcand in https://github.com/nebari-dev/nebari/pull/2227


**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2023.12.1...2024.1.1

## Release 2023.12.1 - December 15, 2023

### Feature changes and enhancements

* Upgrade conda-store to latest version 2023.10.1
* Minor improvements and bug fixes

### Breaking Changes

> WARNING: Prefect, ClearML and kbatch were removed in this release and upgrading to this version will result in all of them being uninstalled.

### What's Changed
* BUG: fix incorrect config override #2086 by @fangchenli in https://github.com/nebari-dev/nebari/pull/2087
* ENH: add AWS IAM permissions_boundary option #2078 by @fangchenli in https://github.com/nebari-dev/nebari/pull/2082
* CI: cleanup local integration workflow by @fangchenli in https://github.com/nebari-dev/nebari/pull/2079
* ENH: check missing GCP services by @fangchenli in https://github.com/nebari-dev/nebari/pull/2036
* ENH: use packaging for version parsing, add unit tests by @fangchenli in https://github.com/nebari-dev/nebari/pull/2048
* ENH: specify required field when retrieving available gcp regions by @fangchenli in https://github.com/nebari-dev/nebari/pull/2033
* Upgrade conda-store to 2023.10.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/2092
* Add upgrade command for 2023.11.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/2103
* CLN: cleanup typing and typing import in init by @fangchenli in https://github.com/nebari-dev/nebari/pull/2107
* Remove kbatch, prefect and clearml by @iameskild in https://github.com/nebari-dev/nebari/pull/2101
* Fix integration tests, helm-validate script by @iameskild in https://github.com/nebari-dev/nebari/pull/2102
* Re-enable AWS tags support by @iameskild in https://github.com/nebari-dev/nebari/pull/2096
* Update upgrade instructions for 2023.11.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/2112
* Update nebari-git env pins by by @iameskild in https://github.com/nebari-dev/nebari/pull/2113
* Update release notes for 2023.11.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/2114


**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2023.11.1...2023.12.1

## Release 2023.11.1 - November 15, 2023

### Feature changes and enhancements

* Upgrade conda-store to latest version 2023  .10.1
* Minor improvements and bug fixes

### Breaking Changes

> WARNING: Prefect, ClearML and kbatch were removed in this release and upgrading to this version will result in all of them being uninstalled.

### What's Changed
* BUG: fix incorrect config override #2086 by @fangchenli in https://github.com/nebari-dev/nebari/pull/2087
* ENH: add AWS IAM permissions_boundary option #2078 by @fangchenli in https://github.com/nebari-dev/nebari/pull/2082
* CI: cleanup local integration workflow by @fangchenli in https://github.com/nebari-dev/nebari/pull/2079
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/2099
* ENH: check missing GCP services by @fangchenli in https://github.com/nebari-dev/nebari/pull/2036
* ENH: use packaging for version parsing, add unit tests by @fangchenli in https://github.com/nebari-dev/nebari/pull/2048
* ENH: specify required field when retrieving available gcp regions by @fangchenli in https://github.com/nebari-dev/nebari/pull/2033
* Upgrade conda-store to 2023.10.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/2092
* Add upgrade command for 2023.11.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/2103
* CLN: cleanup typing and typing import in init by @fangchenli in https://github.com/nebari-dev/nebari/pull/2107
* Remove kbatch, prefect and clearml by @iameskild in https://github.com/nebari-dev/nebari/pull/2101
* Fix integration tests, helm-validate script by @iameskild in https://github.com/nebari-dev/nebari/pull/2102
* Re-enable AWS tags support by @iameskild in https://github.com/nebari-dev/nebari/pull/2096
* Update upgrade instructions for 2023.11.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/2112
* Update nebari-git env pins by by @iameskild in https://github.com/nebari-dev/nebari/pull/2113
* Update release notes for 2023.11.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/2114


**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2023.10.1...2023.11.1


## Release 2023.10.1 - October 20, 2023

This release includes a major refactor which introduces a Pluggy-based extension mechanism which allow developers to build new stages. This is the initial implementation
of the extension mechanism and we expect the interface to be refined overtime. If you're interested in developing your own stage plugin, please refer to [our documentation](https://www.nebari.dev/docs/how-tos/nebari-extension-system#developing-an-extension). When you're ready to upgrade, please download this version from either PyPI or Conda-Forge and run the `nebari upgrade -c nebari-config.yaml`
command and follow the instructions

> WARNING: CDS Dashboards was removed in this release and upgrading to this version will result in CDS Dashboards being uninstalled. A replacement dashboarding solution is currently in the works
> and will be integrated soon.

> WARNING: Given the scope of changes in this release, we highly recommend backing up your system before upgrading. Please refer to our [Manual Backup](https://www.nebari.dev/docs/how-tos/manual-backup) documentation for more details.

### Feature changes and enhancements

* Extension Mechanism Implementation in [PR 1833](https://github.com/nebari-dev/nebari/pull/1833)
  * This also includes much stricter schema validation.
* JupyterHub upgraded to 3.1 in [PR 1856](https://github.com/nebari-dev/nebari/pull/1856)'

### Breaking Changes

* While we have tried our best to avoid breaking changes when introducing the extension mechanism, the scope of the changes is too large for us to confidently say there won't be breaking changes.

> WARNING: CDS Dashboards was removed in this release and upgrading to this version will result in CDS Dashboards being uninstalled. A replacement dashboarding solution is currently in the work and will be integrated soon.

> WARNING: We will be removing and ending support for ClearML, Prefect and kbatch in the next release. The kbatch has been functionally replaced by Argo-Jupyter-Scheduler. We have seen little interest in ClearML and Prefect in recent years, and removing makes sense at this point. However if you wish to continue using them with Nebari we encourage you to [write your own Nebari extension](https://www.nebari.dev/docs/how-tos/nebari-extension-system#developing-an-extension).

### What's Changed
* Spinup spot instance for CI with cirun by @aktech in https://github.com/nebari-dev/nebari/pull/1882
* Fix argo-viewer service account reference by @iameskild in https://github.com/nebari-dev/nebari/pull/1881
* Framework for Nebari deployment via pytest for extensive testing by @aktech in https://github.com/nebari-dev/nebari/pull/1867
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/1878
* Test GCP/AWS Deployment with Pytest by @aktech in https://github.com/nebari-dev/nebari/pull/1871
* Bump DigitalOcean provider to latest by @aktech in https://github.com/nebari-dev/nebari/pull/1891
* Ensure path is Path object by @iameskild in https://github.com/nebari-dev/nebari/pull/1888
* enabling viewing hidden files in jupyterlab file explorer by @kalpanachinnappan in https://github.com/nebari-dev/nebari/pull/1893
* Extension Mechanism Implementation by @costrouc in https://github.com/nebari-dev/nebari/pull/1833
* Fix import path in deployment tests & misc by @aktech in https://github.com/nebari-dev/nebari/pull/1908
* pytest:ensure failure on warnings by @costrouc in https://github.com/nebari-dev/nebari/pull/1907
* workaround for mixed string/posixpath error by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/1915
* ENH: Remove aws cli, use boto3 by @fangchenli in https://github.com/nebari-dev/nebari/pull/1920
* paginator for boto3 ec2 instance types by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/1923
* Update README.md -- fix typo. by @teoliphant in https://github.com/nebari-dev/nebari/pull/1925
* Add more unit tests, add cleanup step for Digital Ocean integration test by @iameskild in https://github.com/nebari-dev/nebari/pull/1910
* Add cleanup step for AWS integration test, ensure disable_prompt is passed through by @iameskild in https://github.com/nebari-dev/nebari/pull/1921
* K8s 1.25 + More Improvements by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/1856
* adding lifecycle ignore to eks node group by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/1905
* nebari init unit tests by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/1931
* Bug fix - JH singleuser environment getting overwritten by @kenafoster in https://github.com/nebari-dev/nebari/pull/1933
* Allow users to specify the Azure RG to deploy into by @iameskild in https://github.com/nebari-dev/nebari/pull/1927
* nebari validate unit tests by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/1938
* adding openid connect provider to enable irsa feature by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/1903
* nebari upgrade CLI tests by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/1963
* CI: Add test coverage by @fangchenli in https://github.com/nebari-dev/nebari/pull/1959
* nebari cli environment variable handling, support, keycloak, dev tests by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/1968
* CI: remove empty notebook to fix pre-commit json check by @fangchenli in https://github.com/nebari-dev/nebari/pull/1976
* TYP: fix typing error in plugins by @fangchenli in https://github.com/nebari-dev/nebari/pull/1973
* TYP: fix return class type in hookimpl by @fangchenli in https://github.com/nebari-dev/nebari/pull/1975
* Allow users to specify Azure tags by @iameskild in https://github.com/nebari-dev/nebari/pull/1967
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/1979
* Do not try and add argo envs when disabled by @iameskild in https://github.com/nebari-dev/nebari/pull/1926
* Handle region with care, updates to test suite by @iameskild in https://github.com/nebari-dev/nebari/pull/1930
* remove custom auth from config schema by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/1994
* CLI: handle removed dns options in deploy command by @fangchenli in https://github.com/nebari-dev/nebari/pull/1992
* Add API docs by @kcpevey in https://github.com/nebari-dev/nebari/pull/1634
* Upgrade images for jupyterhub-ssh, kbatch by @iameskild in https://github.com/nebari-dev/nebari/pull/1997
* Add permissions to generate_cli_docs workflow by @iameskild in https://github.com/nebari-dev/nebari/pull/2005
* standardize regex and messaging for names by @kenafoster in https://github.com/nebari-dev/nebari/pull/2003
* ENH: specify required fields when retrieving available gcp projects by @fangchenli in https://github.com/nebari-dev/nebari/pull/2008
* Modify JupyterHub networkPolicy to match existing policy by @iameskild in https://github.com/nebari-dev/nebari/pull/1991
* Update package dependencies by @iameskild in https://github.com/nebari-dev/nebari/pull/1986
* CI: Add AWS integration test workflow, clean up   by @iameskild in https://github.com/nebari-dev/nebari/pull/1977
* BUG: fix unboundlocalerror in integration test by @fangchenli in https://github.com/nebari-dev/nebari/pull/1999
* Auth0/Github auth-provider config validation fix by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/2009
* terraform upgrade to 1.5.7 by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/1998
* cli init repo auto provision fix by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/2012
* Add gcp_cleanup, minor changes by @iameskild in https://github.com/nebari-dev/nebari/pull/2010
* Fix #2024 by @dcmcand in https://github.com/nebari-dev/nebari/pull/2025
* Upgrade conda-store to 2023.9.2 by @iameskild in https://github.com/nebari-dev/nebari/pull/2028
* Add upgrade steps, instructions for 2023.9.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/2029
* CI: add gcp integration test by @fangchenli in https://github.com/nebari-dev/nebari/pull/2049
* CLN: remove flake8 from dependencies by @fangchenli in https://github.com/nebari-dev/nebari/pull/2044
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/2047
* fix typo in guided init for Digital Ocean by @dcmcand in https://github.com/nebari-dev/nebari/pull/2059
* CI: add do integration by @fangchenli in https://github.com/nebari-dev/nebari/pull/2060
* TYP: make all subfolders under kubernetes_services/template non-module by @fangchenli in https://github.com/nebari-dev/nebari/pull/2043
* TYP: fix most typing errors in provider by @fangchenli in https://github.com/nebari-dev/nebari/pull/2038
* Fix link to documentation on Nebari Deployment home page by @aktech in https://github.com/nebari-dev/nebari/pull/2063
* TST: enable timeout config in playwright notebook test by @fangchenli in https://github.com/nebari-dev/nebari/pull/1996
* DEPS: sync supported python version by @fangchenli in https://github.com/nebari-dev/nebari/pull/2065
* Test support for Python 3.12 by @aktech in https://github.com/nebari-dev/nebari/pull/2046
* BUG: fix validation error related to `provider` #2054 by @fangchenli in https://github.com/nebari-dev/nebari/pull/2056
* CI: improve unit test workflow in CI, revert #2046 by @fangchenli in https://github.com/nebari-dev/nebari/pull/2071
* TST: enable exact_match config in playwright notebook test by @fangchenli in https://github.com/nebari-dev/nebari/pull/2027
* CI: move conda build test to separate job by @fangchenli in https://github.com/nebari-dev/nebari/pull/2073
* Revert conda-store to v0.4.14, #2028 by @iameskild in https://github.com/nebari-dev/nebari/pull/2074
* ENH/CI: add mypy config, and CI workflow by @fangchenli in https://github.com/nebari-dev/nebari/pull/2066
* Update upgrade for 2023.10.1 by @kenfoster in https://github.com/nebari-dev/nebari/pull/2080
* Update RELEASE notes, minor fixes by @iameskild in https://github.com/nebari-dev/nebari/pull/2039

### New Contributors
* @kalpanachinnappan made their first contribution in https://github.com/nebari-dev/nebari/pull/1893
* @fangchenli made their first contribution in https://github.com/nebari-dev/nebari/pull/1920
* @teoliphant made their first contribution in https://github.com/nebari-dev/nebari/pull/1925
* @kenafoster made their first contribution in https://github.com/nebari-dev/nebari/pull/1933
* @dcmcand made their first contribution in https://github.com/nebari-dev/nebari/pull/2025

**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2023.7.2...2023.10.1


## Release 2023.7.2 - August 3, 2023

This is a hot-fix release that resolves an issue whereby users in the `analyst` group are unable to launch their JupyterLab server because the name of the viewer-specific `ARGO_TOKEN` was mislabeled; see [PR 1881](https://github.com/nebari-dev/nebari/pull/1881) for more details.

### What's Changed
* Fix argo-viewer service account reference by @iameskild in https://github.com/nebari-dev/nebari/pull/1881
* Add release notes for 2023.7.2, update release notes for 2023.7.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/1886


## Release 2023.7.1 - July 21, 2023

> WARNING: CDS Dashboards will be deprecated soon. Nebari `2023.7.1` will be the last release with support for CDS Dashboards integration. A new dashboard sharing mechanism added in the near future, but some releases in the interim will not have dashboard sharing capabilities..

> WARNING: For those running on AWS, upgrading from previous versions to `2023.7.1` requires a [backup](https://www.nebari.dev/docs/how-tos/manual-backup). Due to changes made to the VPC (See [issue 1884](https://github.com/nebari-dev/nebari/issues/1884) for details), Terraform thinks it needs to destroy and reprovision a new VPC which causes the entire cluster to be destroyed and rebuilt.

### Feature changes and enhancements

* Addition of Nebari-Workflow-Controller in [PR 1741](https://github.com/nebari-dev/nebari/pull/1741)
* Addition of Argo-Jupyter-Scheduler in [PR 1832](https://github.com/nebari-dev/nebari/pull/1832)
* Make most of the API private

### Breaking Changes

* As mentioned in the above WARNING, clusters running on AWS should perform a [manual backup](https://www.nebari.dev/docs/how-tos/manual-backup) before running the upgrade to the latest version as changes to the AWS VPC will cause the cluster to be destroyed and redeployed.


### What's Changed
* use conda forge explicitly in conda build test by @pmeier in https://github.com/nebari-dev/nebari/pull/1771
* document that the upgrade command is for all nebari upgrades by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/1794
* don't fail CI matrices fast by @pmeier in https://github.com/nebari-dev/nebari/pull/1804
* unvendor keycloak_metrics_spi by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/1810
* Dedent fail-fast by @iameskild in https://github.com/nebari-dev/nebari/pull/1815
* support deploying on existing vpc on aws by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/1807
* purge most danlging qhub references by @pmeier in https://github.com/nebari-dev/nebari/pull/1802
* Add Argo Workflow Admission controller by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/1741
* purge infracost CLI command / CI jobs by @pmeier in https://github.com/nebari-dev/nebari/pull/1820
* remove unused function parameters and CLI flags by @pmeier in https://github.com/nebari-dev/nebari/pull/1725
* purge docs and nox by @pmeier in https://github.com/nebari-dev/nebari/pull/1801
* Add Helm chart lint tool by @viniciusdc in https://github.com/nebari-dev/nebari/pull/1679
* don't set /etc/hosts in CI by @pmeier in https://github.com/nebari-dev/nebari/pull/1729
* remove execute permissions on templates by @pmeier in https://github.com/nebari-dev/nebari/pull/1798
* fix deprecated file deletion by @pmeier in https://github.com/nebari-dev/nebari/pull/1799
* make nebari API private by @pmeier in https://github.com/nebari-dev/nebari/pull/1778
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/1831
* Simplify CI by @iameskild in https://github.com/nebari-dev/nebari/pull/1819
* Fix edge-case where k8s_version is equal to HIGHEST_SUPPORTED_K8S_VER… by @iameskild in https://github.com/nebari-dev/nebari/pull/1842
* add more configuration to enable private clusters on AWS by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/1841
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/1851
* AWS gov cloud support by @sblair-metrostar in https://github.com/nebari-dev/nebari/pull/1857
* Pathlib everywhere by @pmeier in https://github.com/nebari-dev/nebari/pull/1773
* Initial playwright setup by @kcpevey in https://github.com/nebari-dev/nebari/pull/1665
* Changes required for Jupyter-Scheduler integration  by @iameskild in https://github.com/nebari-dev/nebari/pull/1832
* Update upgrade command in preparation for release by @iameskild in https://github.com/nebari-dev/nebari/pull/1868
* Add release notes by @iameskild in https://github.com/nebari-dev/nebari/issues/1869

### New Contributors
* @sblair-metrostar made their first contribution in https://github.com/nebari-dev/nebari/pull/1857

**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2023.5.1...2023.7.1


### Release 2023.5.1 - May 5, 2023

### Feature changes and enhancements

* Upgrade Argo-Workflows to version 3.4.4

### Breaking Changes

* The Argo-Workflows version upgrade will result in a breaking change if the existing Kubernetes CRDs are not deleted (see the NOTE below for more details).
* There is a minor breaking change for the Nebari CLI version shorthand, previously it `nebari -v` and now to align with Python convention, it will be `nebari -V`.

> NOTE: After installing the Nebari version `2023.5.1`, please run `nebari upgrade -c nebari-config.yaml` to upgrade
> the `nebari-config.yaml`. This command will also prompt you to delete a few Kubernetes resources (specifically
> the Argo-Workflows CRDS and service accounts) before you can upgrade.

### What's Changed
* Use --quiet flag for conda install in CI by @pmeier in https://github.com/nebari-dev/nebari/pull/1699
* improve CLI tests by @pmeier in https://github.com/nebari-dev/nebari/pull/1710
* Fix Existing dashboards by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/1723
* Fix dashboards by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/1727
* Typo in the conda-store <-> conda_store key by @costrouc in https://github.com/nebari-dev/nebari/pull/1740
* use -V (upper case) for --version short form by @pmeier in https://github.com/nebari-dev/nebari/pull/1720
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/1692
* improve pytest configuration by @pmeier in https://github.com/nebari-dev/nebari/pull/1700
* fix upgrade command to look for nebari_version instead of qhub_version by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/1693
* remove lazy import by @pmeier in https://github.com/nebari-dev/nebari/pull/1721
* fix nebari invocation through python by @pmeier in https://github.com/nebari-dev/nebari/pull/1711
* Update Argo Workflows to latest version by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/1639
* Update secret token in release-notes-sync action by @pavithraes in https://github.com/nebari-dev/nebari/pull/1753
* Typo fix in release-notes-sync action by @pavithraes in https://github.com/nebari-dev/nebari/pull/1756
* 🔄 Synced file(s) with nebari-dev/.github by @nebari-sensei in https://github.com/nebari-dev/nebari/pull/1758
* Update path in release-notes-sync action by @pavithraes in https://github.com/nebari-dev/nebari/pull/1757
* Updating heading format in release notes by @pavithraes in https://github.com/nebari-dev/nebari/pull/1761
* Update vault url by @costrouc in https://github.com/nebari-dev/nebari/pull/1752
* Fix? contributor test trigger by @pmeier in https://github.com/nebari-dev/nebari/pull/1734
* Consistent user Experience with y/N. by @AM-O7 in https://github.com/nebari-dev/nebari/pull/1747
* Fix contributor trigger by @pmeier in https://github.com/nebari-dev/nebari/pull/1765
* add more debug output to contributor test trigger by @pmeier in https://github.com/nebari-dev/nebari/pull/1766
* fix copy-paste error by @pmeier in https://github.com/nebari-dev/nebari/pull/1767
* add instructions insufficient permissions of contributor trigger by @pmeier in https://github.com/nebari-dev/nebari/pull/1772
* fix invalid escape sequence by @pmeier in https://github.com/nebari-dev/nebari/pull/1770
* Update AMI  in `.cirun.yml` for nebari-dev-ci AWS account by @aktech in https://github.com/nebari-dev/nebari/pull/1776
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/1768
* turn warnings into errors with pytest by @pmeier in https://github.com/nebari-dev/nebari/pull/1774
* purge setup.cfg by @pmeier in https://github.com/nebari-dev/nebari/pull/1781
* improve pre-commit run on GHA by @pmeier in https://github.com/nebari-dev/nebari/pull/1782
* Upgrade to k8s 1.24 by @iameskild in https://github.com/nebari-dev/nebari/pull/1760
* Overloaded dask gateway fix by @Adam-D-Lewis in https://github.com/nebari-dev/nebari/pull/1777
* Add option to specify GKE release channel by @iameskild in https://github.com/nebari-dev/nebari/pull/1648
* Update upgrade command, add RELEASE notes by @iameskild in https://github.com/nebari-dev/nebari/pull/1789

### New Contributors
* @pmeier made their first contribution in https://github.com/nebari-dev/nebari/pull/1699
* @AM-O7 made their first contribution in https://github.com/nebari-dev/nebari/pull/1747

**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2023.4.1...2023.5.1


## Release 2023.4.1 - April 12, 2023

> NOTE: Nebari requires Kubernetes version 1.23 and Digital Ocean now requires new clusters to run Kubernetes version 1.24. This means that if you are currently running on Digital Ocean, you should be fine but deploying on a new cluster on Digital Ocean is not possible until we upgrade Kubernetes version (see [issue 1622](https://github.com/nebari-dev/nebari/issues/1622) for more details).


### Feature changes and enhancements

* Upgrades and improvements to conda-store including a new user-interface and greater administrator capabilities.
* Idle-culler settings can now be configured directly from the `nebari-config.yaml`.


### What's Changed
* PR: Raise timeout for jupyter session by @ppwadhwa in https://github.com/nebari-dev/nebari/pull/1646
* PR lower dashboard launch timeout by @ppwadhwa in https://github.com/nebari-dev/nebari/pull/1647
* PR: Update dashboard environment by @ppwadhwa in https://github.com/nebari-dev/nebari/pull/1655
* Fix doc link in README.md by @tkoyama010 in https://github.com/nebari-dev/nebari/pull/1660
* PR: Update dask environment by @ppwadhwa in https://github.com/nebari-dev/nebari/pull/1654
* Feature remove jupyterlab news by @costrouc in https://github.com/nebari-dev/nebari/pull/1641
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/1644
* Feat GitHub actions before_script and after_script steps by @costrouc in https://github.com/nebari-dev/nebari/pull/1672
* Remove examples folder by @ppwadhwa in https://github.com/nebari-dev/nebari/pull/1664
* Fix GH action typos by @kcpevey in https://github.com/nebari-dev/nebari/pull/1677
* Github Actions CI needs id-token write permissions by @costrouc in https://github.com/nebari-dev/nebari/pull/1682
* Update AWS force destroy script, include lingering volumes by @iameskild in https://github.com/nebari-dev/nebari/pull/1681
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/1673
* Make idle culler settings configurable from the `nebari-config.yaml` by @iameskild in https://github.com/nebari-dev/nebari/pull/1689
* Update pyproject dependencies and add test to ensure it builds on conda-forge by @iameskild in https://github.com/nebari-dev/nebari/pull/1662
* Retrieve secrets from Vault, fix test-provider CI by @iameskild in https://github.com/nebari-dev/nebari/pull/1676
* Pull PyPI secrets from Vault by @iameskild in https://github.com/nebari-dev/nebari/pull/1696
* Adding newest conda-store 0.4.14 along with superadmin credentials by @costrouc in https://github.com/nebari-dev/nebari/pull/1701
* Update release notes for 2023.4.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/1722

### New Contributors
* @ppwadhwa made their first contribution in https://github.com/nebari-dev/nebari/pull/1646
* @tkoyama010 made their first contribution in https://github.com/nebari-dev/nebari/pull/1660

**Full Changelog**: https://github.com/nebari-dev/nebari/compare/2023.1.1...2023.4.1

## Release 2023.1.1 - January 30, 2023

### What's Changed
* 🔄 Synced file(s) with nebari-dev/.github by @nebari-sensei in https://github.com/nebari-dev/nebari/pull/1588
* Make conda-store file system read-only by default by @alimanfoo in https://github.com/nebari-dev/nebari/pull/1595
* ENH - Switch to ruff and pre-commit.ci by @trallard in https://github.com/nebari-dev/nebari/pull/1602
* Migrate to hatch by @iameskild in https://github.com/nebari-dev/nebari/pull/1545
* Add check_repository_cred function to CLI by @iameskild in https://github.com/nebari-dev/nebari/pull/1605
* Adding jupyterlab-conda-store extension support to Nebari by @costrouc in https://github.com/nebari-dev/nebari/pull/1564
* [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/nebari-dev/nebari/pull/1613
* Ensure Argo-Workflow controller containerRuntimeExecutor is set to emissary by @iameskild in https://github.com/nebari-dev/nebari/pull/1614
* Pass `secret_name` to TF scripts when certificate type = existing by @iameskild in https://github.com/nebari-dev/nebari/pull/1621
* Pin Nebari dependencies, set k8s version for GKE by @iameskild in https://github.com/nebari-dev/nebari/pull/1624
* Create aws-force-destroy bash script by @iameskild in https://github.com/nebari-dev/nebari/pull/1611
* Add option for AWS node-groups to run in a single subnet/AZ by @iameskild in https://github.com/nebari-dev/nebari/pull/1428
* Add export-users to keycloak CLI command, add dev CLI command by @iameskild in https://github.com/nebari-dev/nebari/pull/1610
* Unpin packages in default dashboard env by @iameskild in https://github.com/nebari-dev/pull/1628
* Add release notes for 2023.1.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/1629
* Set GKE release_channel to unspecified to prevent auto k8s updates by @iameskild in https://github.com/nebari-dev/nebari/pull/1630
* Update default nebari-dask, nebari image tags by @iameskild in https://github.com/nebari-dev/nebari/pull/1636

### New Contributors
* @pre-commit-ci made their first contribution in https://github.com/nebari-dev/nebari/pull/1613


## Release 2022.11.1 - December 1, 2022

### What's Changed

* cherry-pick Update README logo (#1514) by @aktech in https://github.com/nebari-dev/nebari/pull/1517
* Release/2022.10.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/1527
* Add Note about QHub->Nebari rename in old docs by @pavithraes in https://github.com/nebari-dev/nebari/pull/1543
* 🔄 Synced file(s) with nebari-dev/.github by @nebari-sensei in https://github.com/nebari-dev/nebari/pull/1550
* 🔄 Synced file(s) with nebari-dev/.github by @nebari-sensei in https://github.com/nebari-dev/nebari/pull/1551
* 🔄 Synced file(s) with nebari-dev/.github by @nebari-sensei in https://github.com/nebari-dev/nebari/pull/1555
* 🔄 Synced file(s) with nebari-dev/.github by @nebari-sensei in https://github.com/nebari-dev/nebari/pull/1560
* Small CLI fixes by @iameskild in https://github.com/nebari-dev/nebari/pull/1529
* 🔄 Synced file(s) with nebari-dev/.github by @nebari-sensei in https://github.com/nebari-dev/nebari/pull/1561
* Render github actions configurations as yaml by @aktech in https://github.com/nebari-dev/nebari/pull/1528
* Update "QHub" to "Nebari" in example notebooks by @pavithraes in https://github.com/nebari-dev/nebari/pull/1556
* Update links to Nebari docs in guided init by @pavithraes in https://github.com/nebari-dev/nebari/pull/1557
* CI: Spinup unique cirun runners for each job by @aktech in https://github.com/nebari-dev/nebari/pull/1563
* Issue-1417: Improve Dask workers placement on AWS | fixing a minor typo by @limacarvalho in https://github.com/nebari-dev/nebari/pull/1487
* Update `setup-node` version by @iameskild in https://github.com/nebari-dev/nebari/pull/1570
* Facilitate CI run for contributor PR by @aktech in https://github.com/nebari-dev/nebari/pull/1568
* Action to sync release notes with nebari-docs by @pavithraes in https://github.com/nebari-dev/nebari/pull/1554
* Restore how the dask worker node group is selected by default by @iameskild in https://github.com/nebari-dev/nebari/pull/1577
* Fix skip check for workflows by @aktech in https://github.com/nebari-dev/nebari/pull/1578
* 📝 Update readme by @trallard in https://github.com/nebari-dev/nebari/pull/1579
* MAINT - Miscellaneous maintenance tasks by @trallard in https://github.com/nebari-dev/nebari/pull/1580
* Wait for Test PyPI to upload test release by @iameskild in https://github.com/nebari-dev/nebari/pull/1583
* Add release notes for 2022.11.1 by @iameskild in https://github.com/nebari-dev/nebari/pull/1584


### New Contributors
* @nebari-sensei made their first contribution in https://github.com/nebari-dev/nebari/pull/1550
* @limacarvalho made their first contribution in https://github.com/nebari-dev/nebari/pull/1487


## Release 2022.10.1 - October 28, 2022

### **WARNING**

> The project has recently been renamed from QHub to Nebari. If your deployment is is still managed by `qhub`, performing an inplace upgrade will **IRREVOCABLY BREAK** your deployment. This will cause you to lose any data stored on the platform, including but not limited to, NFS (filesystem) data, conda-store environments, Keycloak users and groups, etc. Please [backup](https://www.nebari.dev/docs/how-tos/manual-backup) your data before attempting an upgrade.


### Feature changes and enhancements

We are happy to announce the first official release of Nebari (formly QHub)! This release lays the groundwork for many exciting new features and improvements to come.

This release introduces several important changes which include:
- a major project name change from QHub to Nebari - [PR 1508](https://github.com/nebari-dev/nebari/pull/1508)
- a switch from the SemVer to CalVer versioning format - [PR 1501](https://github.com/nebari-dev/nebari/pull/1501)
- a new, Typer-based CLI for improved user experience - [PR 1443](https://github.com/Quansight/qhub/pull/1443) + [PR 1519](https://github.com/nebari-dev/nebari/pull/1519)

Although breaking changes are never fun, the Nebari development team believes these changes are important for the immediate and future success of the project. If you experience any issues or have any questions about these changes, feel free to open an [issue on our Github repo](https://github.com/nebari-dev/nebari/issues).


### What's Changed
* Switch to CalVer by @iameskild in https://github.com/nebari-dev/nebari/pull/1501
* Update theme welcome messages to use Nebari by @pavithraes in https://github.com/nebari-dev/nebari/pull/1503
* Name change QHub --> Nebari by @iameskild in https://github.com/nebari-dev/nebari/pull/1508
* qhub/initialize: lazy load attributes that require remote information by @FFY00 in https://github.com/nebari-dev/nebari/pull/1509
* Update README logo reference by @viniciusdc in https://github.com/nebari-dev/nebari/pull/1514
* Add fix, enhancements and pytests for CLI by @iameskild in https://github.com/nebari-dev/nebari/pull/1498
* Remove old CLI + cleanup by @iameskild in https://github.com/nebari-dev/nebari/pull/1519
* Update `skip_remote_state_provision` default value by @viniciusdc in https://github.com/nebari-dev/nebari/pull/1521
* Add release notes for 2022.10.1 in https://github.com/nebari-dev/nebari/pull/1523

### New Contributors
* @pavithraes made their first contribution in https://github.com/nebari-dev/nebari/pull/1503
* @FFY00 made their first contribution in https://github.com/nebari-dev/nebari/pull/1509

**Note: The following releases (v0.4.5 and lower) were made under the name `Quansight/qhub`.**

## Release v0.4.5 - October 14, 2022

Enhancements for this release include:

- Fix reported bug with Azure deployments due to outdated azurerm provider
- All dashboards related conda-store environments are now visible as options for spawning dashboards
- New Nebari entrypoint
- New Typer-based CLI for Qhub (available using new entrypoint)
- Renamed built-in conda-store namespaces and added customization support
- Updated Traefik version to support the latest Kubernetes API

### What's Changed
* Update azurerm version by @tjcrone in https://github.com/Quansight/qhub/pull/1471
* Make CDSDashboards.conda_envs dynamically update from function by @costrouc in https://github.com/Quansight/qhub/pull/1358
* Fix get_latest_repo_tag fn by @iameskild in https://github.com/Quansight/qhub/pull/1485
* Nebari Typer CLI  by @asmijafar20 in https://github.com/Quansight/qhub/pull/1443
* Pass AWS `region`, `kubernetes_version` to terraform scripts by @iameskild in https://github.com/Quansight/qhub/pull/1493
* Enable ebs-csi driver on AWS, add region + kubernetes_version vars by @iameskild in https://github.com/Quansight/qhub/pull/1494
* Update traefik version + CRD by @iameskild in https://github.com/Quansight/qhub/pull/1489
* [ENH] Switch default and filesystem name envs by @viniciusdc in https://github.com/Quansight/qhub/pull/1357

### New Contributors
* @tjcrone made their first contribution in https://github.com/Quansight/qhub/pull/1471

### Migration note

If you are upgrading from a version of Nebari prior to `0.4.5`, you will need to manually update your conda-store namespaces
to be compatible with the new Nebari version. This is a one-time migration step that will need to be performed after upgrading to continue using the service. Refer to [How to migrate base conda-store namespaces](https://deploy-preview-178--nebari-docs.netlify.app/troubleshooting#conda-store-compatibility-migration-steps-when-upgrading-to-045) for further instructions.

## Release v0.4.4 - September 22, 2022

### Feature changes and enhancements

Enhancements for this release include:
- Bump `conda-store` version to `v0.4.11` and enable overrides
- Fully decouple the JupyterLab, JupyterHub and Dask-Worker images from the main codebase
  - See https://github.com/nebari-dev/nebari-docker-images for images
- Add support for Python 3.10
- Add support for Terraform binary download for M1 Mac
- Add option to supply additional arguments to ingress from qhub-config.yaml
- Add support for Kubernetes Kind (local)

### What's Changed
* Add support for terraform binary download for M1 by @aktech in https://github.com/Quansight/qhub/pull/1370
* Improvements in the QHub Cost estimate tool by @HarshCasper in https://github.com/Quansight/qhub/pull/1365
* Add Python-3.10 by @HarshCasper in https://github.com/Quansight/qhub/pull/1352
* Add backwards compatibility item to test checklist by @viniciusdc in https://github.com/Quansight/qhub/pull/1381
* add code server version to fix build by @HarshCasper in https://github.com/Quansight/qhub/pull/1383
* Update Cirun.io config to use labels by @aktech in https://github.com/Quansight/qhub/pull/1379
* Decouple docker images by @iameskild in https://github.com/Quansight/qhub/pull/1371
* Set LATEST_SUPPORTED_PYTHON_VERSION as str by @iameskild in https://github.com/Quansight/qhub/pull/1387
* Integrate kind into local deployment to no longer require minikube for development by @costrouc in https://github.com/Quansight/qhub/pull/1171
* Upgrade conda-store to 0.4.7 allow for customization by @costrouc in https://github.com/Quansight/qhub/pull/1385
* [ENH] Bump conda-store to v0.4.9 by @viniciusdc in https://github.com/Quansight/qhub/pull/1392
* [ENH] Add `pyarrow` and `s3fs` by @viniciusdc in https://github.com/Quansight/qhub/pull/1393
* Fixing bug in authentication method in Conda-Store authentication by @costrouc in https://github.com/Quansight/qhub/pull/1396
* CI: Merge test and release to PyPi workflows into one by @HarshCasper in https://github.com/Quansight/qhub/pull/1386
* Update packages in the dashboard env by @iameskild in https://github.com/Quansight/qhub/pull/1402
* BUG: Setting behind proxy setting in conda-store to be aware of http vs. https by @costrouc in https://github.com/Quansight/qhub/pull/1404
* Minor update to release workflow by @iameskild in https://github.com/Quansight/qhub/pull/1406
* Clean up release workflow by @iameskild in https://github.com/Quansight/qhub/pull/1407
* Add release notes for v0.4.4 by @iameskild in https://github.com/Quansight/qhub/pull/1408
* Update Ingress overrides behaviour by @viniciusdc in https://github.com/Quansight/qhub/pull/1420
* Preserve conda-store image permissions by @iameskild in https://github.com/Quansight/qhub/pull/1419
* Add project name to jhub helm chart release name by @iameskild in https://github.com/Quansight/qhub/pull/1422
* Fix for helm extension overrides data type issue by @konkapv in https://github.com/Quansight/qhub/pull/1424
* Add option to disable tls certificate by @iameskild in https://github.com/Quansight/qhub/pull/1421
* Fixing provider=existing for local/existing by @costrouc in https://github.com/Quansight/qhub/pull/1425
* Update release, testing checklist by @iameskild in https://github.com/Quansight/qhub/pull/1397
* Add `--disable-checks` flag to deploy by @iameskild in https://github.com/Quansight/qhub/pull/1429
* Adding option to supply additional arguments to ingress via `ingress.terraform_overrides.additional-arguments` by @costrouc in https://github.com/Quansight/qhub/pull/1431
* Add properties to middleware crd headers by @iameskild in https://github.com/Quansight/qhub/pull/1434
* Restart conda-store worker when new conda env is added to config.yaml by @iameskild in https://github.com/Quansight/qhub/pull/1437
* Pin dask ipywidgets version to `7.7.1` by @viniciusdc in https://github.com/Quansight/qhub/pull/1442
* Set qhub-dask version to 0.4.4 by @iameskild in https://github.com/Quansight/qhub/pull/1470

### New Contributors
* @konkapv made their first contribution in https://github.com/Quansight/qhub/pull/1424

## Release v0.4.3 - July 7, 2022

### Feature changes and enhancements

Enhancements for this release include:
- Integrating Argo Workflow
- Integrating kbatch
- Adding `cost-estimate` CLI subcommand (Infracost)
- Add `panel-serve` as a CDS dashboard option
- Add option to use RetroLab instead of default JupyterLab


### What's Changed
* Update the login/Keycloak docs page by @gabalafou in https://github.com/Quansight/qhub/pull/1289
* Add configuration option so myst parser generates anchors for heading… by @costrouc in https://github.com/Quansight/qhub/pull/1299
* Image scanning by @HarshCasper in https://github.com/Quansight/qhub/pull/1291
* Fix display version behavior by @viniciusdc in https://github.com/Quansight/qhub/pull/1275
* [Docs] Add docs about custom Identity providers for Authentication by @viniciusdc in https://github.com/Quansight/qhub/pull/1273
* Add prefect token var to CI when needed by @viniciusdc in https://github.com/Quansight/qhub/pull/1279
* ci: prevent image scans on main image builds by @HarshCasper in https://github.com/Quansight/qhub/pull/1300
* Integrate `kbatch` by @iameskild in https://github.com/Quansight/qhub/pull/1258
* add `retrolab` to the base jupyter image by @tonyfast in https://github.com/Quansight/qhub/pull/1222
* Update pre-commit, remove vale by @iameskild in https://github.com/Quansight/qhub/pull/1282
* Argo Workflows by @Adam-D-Lewis in https://github.com/Quansight/qhub/pull/1252
* Update minio, postgresql chart repo location by @iameskild in https://github.com/Quansight/qhub/pull/1308
* Fix broken AWS, set minimum desired size to 1, enable 0 scaling by @tylerpotts in https://github.com/Quansight/qhub/pull/1304
* v0.4.2 release notes by @iameskild in https://github.com/Quansight/qhub/pull/1323
* install dask lab ext from main by @iameskild in https://github.com/Quansight/qhub/pull/1321
* Overrides default value for dask-labextension by @viniciusdc in https://github.com/Quansight/qhub/pull/1327
* CI: Add Infracost to GHA CI for infra cost tracking by @HarshCasper in https://github.com/Quansight/qhub/pull/1316
* Add check for highest supported k8s version by @aktech in https://github.com/Quansight/qhub/pull/1336
* Increase the default instance sizes by @peytondmurray in https://github.com/Quansight/qhub/pull/1338
* Add panel-serve as a CDS dashboard option by @iameskild in https://github.com/Quansight/qhub/pull/1070
* Generate QHub Costs via `infracost` by @HarshCasper in https://github.com/Quansight/qhub/pull/1340
* Add release-checklist issue template by @iameskild in https://github.com/Quansight/qhub/pull/1314
* Fix missing import: `rich` : broken qhub init with cloud by @aktech in https://github.com/Quansight/qhub/pull/1353
* Bump qhub-dask version to 0.4.3 by @peytondmurray in https://github.com/Quansight/qhub/pull/1341
* Remove the need for AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to be set with Digital Ocean deployment by @costrouc in https://github.com/Quansight/qhub/pull/1344
* Revert "Remove the need for AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to be set with Digital Ocean deployment" by @viniciusdc in https://github.com/Quansight/qhub/pull/1355
* Upgrade kbatch version by @iameskild in https://github.com/Quansight/qhub/pull/1335
* Drop support for python 3.7 in dask environment by @peytondmurray in https://github.com/Quansight/qhub/pull/1354
* Add useful terminal utils to jlab image by @dharhas in https://github.com/Quansight/qhub/pull/1361
* Tweak bashrc by @dharhas in https://github.com/Quansight/qhub/pull/1363
* Fix bug where vscode extensions are not installing by @viniciusdc in https://github.com/Quansight/qhub/pull/1360

### New Contributors
* @gabalafou made their first contribution in https://github.com/Quansight/qhub/pull/1289
* @peytondmurray made their first contribution in https://github.com/Quansight/qhub/pull/1338
* @dharhas made their first contribution in https://github.com/Quansight/qhub/pull/1361

**Full Changelog**: https://github.com/Quansight/qhub/compare/v0.4.1...v0.4.3


## Release v0.4.2 - June 8, 2022

### Incident postmortem

#### Bitnami update breaks post v0.4.0 releases

On June 2, 2022, GitHub user @peytondmurray reported [issue 1306](https://github.com/Quansight/qhub/issues/1306), stating that he was unable to deploy QHub using either the latest release `v0.4.1` or installing `qhub` from `main`. As verified by @peytondmurray and others, during your first `qhub deploy`, the deployment halts and complains about two invalid Helm charts missing from the bitnami `index.yaml`.

[Bitnami's decision to update how long they keep old Helm charts in their index for](https://github.com/bitnami/charts/issues/10539) has essentially broken all post `v0.4.0` versions of QHub.

This is a severe bug that will affect any new user who tries to install and deploy QHub with any version less than `v0.4.2` and greater than or equal to `v0.4.0`.

Given the impact and severity of this bug, the team has decided to quickly cut a hotfix.

#### AWS deployment failing due to old auto-scaler helm chart

On May 27, 2022, GitHub user @tylerpotts reported [issue 1302](https://github.com/Quansight/qhub/issues/1302), stating that he was unable to deploy QHub using the latest release `v0.4.1` (or installing `qhub` from `main`). As described in the original issue, the deployment failed complaining about the deprecated `v1beta` Kubernetes API. This led to the discovery that we were using an outdated `cluster_autoscaler` helm chart.

The solution is to update from `v1beta` to `v1` Kubernetes API for the appropriate resources and update the reference to the `cluster_autoscaler` helm chart.

Given the impact and severity of this bug, the team has decided to quickly cut a hotfix.

### Bug fixes

This release is a hotfix for the issue summarized in the following:
* [issue 1319](https://github.com/Quansight/qhub/issues/1319)
* [issue 1306](https://github.com/Quansight/qhub/issues/1306)
* [issue 1302](https://github.com/Quansight/qhub/issues/1302)


### What's Changed
* Update minio, postgresql chart repo location by @iameskild in [PR 1308](https://github.com/Quansight/qhub/pull/1308)
* Fix broken AWS, set minimum desired size to 1, enable 0 scaling by @tylerpotts in [PR 1304](https://github.com/Quansight/qhub/issues/1304)


## Release v0.4.1 - May 10, 2022

### Feature changes and enhancements

Enhancements for this release include:
- Add support for pinning the IP address of the load balancer via terraform overrides
- Upgrade to Conda-Store to `v0.3.15`
- Add ability to limit JupyterHub profiles based on users/groups

### Bug fixes

This release addresses several bugs with a slight emphasis on stabilizing the core services while also improving the end user experience.

### What's Changed
* [BUG] Adding back feature of limiting profiles for users and groups by @costrouc in [PR 1169](https://github.com/Quansight/qhub/pull/1169)
* DOCS: Add release notes for v0.4.0 release by @HarshCasper in [PR 1170](https://github.com/Quansight/qhub/pull/1170)
* Move ipython config within jupyterlab to docker image with more robust jupyterlab ssh tests by @costrouc in [PR 1143](https://github.com/Quansight/qhub/pull/1143)
* Removing custom dask_gateway from qhub and idle_timeout for dask clusters to 30 min by @costrouc in [PR 1151](https://github.com/Quansight/qhub/pull/1151)
* Overrides.json now managed by qhub configmaps instead of inside docker image by @costrouc in [PR 1173](https://github.com/Quansight/qhub/pull/1173)
* Adding examples to QHub jupyterlab  by @costrouc in [PR 1176](https://github.com/Quansight/qhub/pull/1176)
* Bump conda-store version to 0.3.12 by @costrouc in [PR 1179](https://github.com/Quansight/qhub/pull/1179)
* Fixing concurrency not being specified in configuration by @costrouc in [PR 1180](https://github.com/Quansight/qhub/pull/1180)
* Adding ipykernel as default to environment along with ensure conda-store restarted on config change by @costrouc in [PR 1181](https://github.com/Quansight/qhub/pull/1181)
* keycloak dev docs by @danlester in [PR 1184](https://github.com/Quansight/qhub/pull/1184)
* Keycloakdev2 by @danlester in [PR 1185](https://github.com/Quansight/qhub/pull/1185)
* Setting minio storage to by default be same as filesystem size for Conda-Store environments by @costrouc in [PR 1188](https://github.com/Quansight/qhub/pull/1188)
* Bump Conda-Store version in Qhub to 0.3.13 by @costrouc in [PR 1189](https://github.com/Quansight/qhub/pull/1189)
* Upgrade mrparkers to 3.7.0 by @danlester in [PR 1183](https://github.com/Quansight/qhub/pull/1183)
* Mdformat tables by @danlester in [PR 1186](https://github.com/Quansight/qhub/pull/1186)
* [ImgBot] Optimize images by @imgbot in [PR 1187](https://github.com/Quansight/qhub/pull/1187)
* Bump conda-store version to 0.3.14 by @costrouc in [PR 1192](https://github.com/Quansight/qhub/pull/1192)
* Allow terraform init to upgrade providers within version specification by @costrouc in [PR 1194](https://github.com/Quansight/qhub/pull/1194)
* Adding missing __init__ files by @costrouc in [PR 1196](https://github.com/Quansight/qhub/pull/1196)
* Release 0.3.15 for Conda-Store by @costrouc in [PR 1205](https://github.com/Quansight/qhub/pull/1205)
* Profilegroups by @danlester in [PR 1203](https://github.com/Quansight/qhub/pull/1203)
* Render `.gitignore`, black py files by @iameskild in [PR 1206](https://github.com/Quansight/qhub/pull/1206)
* Update qhub-dask pinned version by @iameskild in [PR 1224](https://github.com/Quansight/qhub/pull/1224)
* Fix env doc links and add corresponding tests by @aktech in [PR 1216](https://github.com/Quansight/qhub/pull/1216)
* Update conda-store-environment variable `type`  by @iameskild in [PR 1213](https://github.com/Quansight/qhub/pull/1213)
* Update release notes - justification for changes in `v0.4.0`  by @iameskild in [PR 1178](https://github.com/Quansight/qhub/pull/1178)
* Support for pinning the IP address of the load balancer via terraform overrides by @aktech in [PR 1235](https://github.com/Quansight/qhub/pull/1235)
* Bump moment from 2.29.1 to 2.29.2 in /tests_e2e by @dependabot in [PR 1241](https://github.com/Quansight/qhub/pull/1241)
* Update cdsdashboards to 0.6.1, Voila to 0.3.5 by @danlester in [PR 1240](https://github.com/Quansight/qhub/pull/1240)
* Bump minimist from 1.2.5 to 1.2.6 in /tests_e2e by @dependabot in [PR 1208](https://github.com/Quansight/qhub/pull/1208)
* output check fix by @Adam-D-Lewis in [PR 1244](https://github.com/Quansight/qhub/pull/1244)
* Update panel version to fix jinja2 recent issue by @viniciusdc in [PR 1248](https://github.com/Quansight/qhub/pull/1248)
* Add support for terraform overrides in cloud and VPC deployment for Azure by @aktech in [PR 1253](https://github.com/Quansight/qhub/pull/1253)
* Add test-release workflow by @iameskild in [PR 1245](https://github.com/Quansight/qhub/pull/1245)
* Bump async from 3.2.0 to 3.2.3 in /tests_e2e by @dependabot in [PR 1260](https://github.com/Quansight/qhub/pull/1260)
* [WIP] Add support for VPC deployment for GCP via terraform overrides by @aktech in [PR 1259](https://github.com/Quansight/qhub/pull/1259)
* Update login instructions for training by @iameskild in [PR 1261](https://github.com/Quansight/qhub/pull/1261)
* Add docs for general node upgrade by @iameskild in [PR 1246](https://github.com/Quansight/qhub/pull/1246)
* [ImgBot] Optimize images by @imgbot in [PR 1264](https://github.com/Quansight/qhub/pull/1264)
* Fix project name and domain at None by @pierrotsmnrd in [PR 856](https://github.com/Quansight/qhub/pull/856)
* Adding name convention validator for QHub project name by @viniciusdc in [PR 761](https://github.com/Quansight/qhub/pull/761)
* Minor doc updates by @iameskild in [PR 1268](https://github.com/Quansight/qhub/pull/1268)
* Enable display of Qhub version by @viniciusdc in [PR 1256](https://github.com/Quansight/qhub/pull/1256)
* Fix missing region from AWS provider by @viniciusdc in [PR 1271](https://github.com/Quansight/qhub/pull/1271)
* Re-enable GPU profiles for GCP/AWS by @viniciusdc in [PR 1219](https://github.com/Quansight/qhub/pull/1219)
* Release notes for `v0.4.1` by @iameskild in [PR 1272](https://github.com/Quansight/qhub/pull/1272)

### New Contributors
* @dependabot made their first contribution in [PR 1241](https://github.com/Quansight/qhub/pull/1241)

[**Full Changelog**](https://github.com/Quansight/qhub/compare/v0.4.0...v0.4.1)

## Release v0.4.0.post1 - April 7, 2022

This post-release addresses the a few minor bugs and updates the release notes.
There are no breaking changes or API changes.

- Render `.gitignore`, black py files - [PR 1206](https://github.com/Quansight/qhub/pull/1206)
- Update qhub-dask pinned version - [PR 1224](https://github.com/Quansight/qhub/pull/1224)
- Update conda-store-environment variable `type` - [PR 1213](https://github.com/Quansight/qhub/pull/1213)
- Update release notes - justification for changes in `v0.4.0` - [PR 1178](https://github.com/Quansight/qhub/pull/1178)
- Merge spawner and profile env vars to ensure dashboard sharing vars are provided to dashboard servers - [PR 1237](https://github.com/Quansight/qhub/pull/1237)

## Release v0.4.0 - March 17, 2022

**WARNING**
> If you're looking for a stable version of QHub, please consider `v0.3.14`. The `v0.4.0` has many breaking changes and has rough edges that will be resolved in upcoming point releases.

We are happy to announce the release of `v0.4.0`! This release lays the groundwork for many exciting new features and improvements in the future, stay tuned.

Version `v0.4.0` introduced many design changes along with a handful of user-facing changes that require some justification. Unfortunately as a result of these changes, QHub
instances that are upgraded from previous version to `v0.4.0` will irrevocably break.

Until we have a fully functioning backup mechanism, anyone looking to upgrade is highly encouraged to backup their data, see the
[upgrade docs](https://docs.qhub.dev/en/latest/source/admin_guide/breaking-upgrade.html) and more specifically, the
[backup docs](https://docs.qhub.dev/en/latest/source/admin_guide/backup.html).

These design changes were considered important enough that the development team felt they were warranted. Below we try to highlight a few of the largest changes
and provide justification for them.

- Replace Terraforms resource targeting with staged Terraform deployments.
  - *Justification*: using Terraform resource targeting was never an ideal way of handing off outputs from stage to the next and Terraform explicitly warns its users that it's only
    intended to be used "for exceptional situations such as recovering from errors or mistakes".
- Fully remove `cookiecutter` as a templating mechanism.
  - *Justification*: Although `cookiecutter` has its benefits, we were becoming overly reliant on it as a means of rendering various scripts needed for the deployment. Reading through
    Terraform scripts with scattered `cookiecutter` statements was increasing troublesome and a bit intimidating. Our IDEs are also much happier about this change.
- Removing users and groups from the `qhub-config.yaml` and replacing user management with Keycloak.
  - *Justification*: Up until now, any change to QHub deployment needed to be made in the `qhub-config.yaml` which had the benefit of centralizing any configuration. However it
    also potentially limited the kinds of user management tasks while also causing the `qhub-config.yaml` to balloon in size. Another benefit of removing users and groups from the
    `qhub-config.yaml` that deserves highlighting is that user management no longer requires a full redeployment.

Although breaking changes are never fun, we hope the reasons outlined above are encouraging signs that we are working on building a better, more stable, more flexible product. If you
experience any issues or have any questions about these changes, feel free to open an [issue on our Github repo](https://github.com/Quansight/qhub/issues).

### Breaking changes

Explicit user facing changes:

- Upgrading to `v0.4.0` will require a filesystem backup given the scope and size of the current change set.
  - Running `qhub upgrade` will produce an updated `qhub-config.yaml` and a JSON file of users that can then be imported into Keycloak.
- With the addition of Keycloak, QHub will no longer support `security.authentication.type = custom`.
  - No more users and groups in the `qhub-config.yaml`.

### Feature changes and enhancements

- Authentication is now managed by Keycloak.
- QHub Helm extension mechanism added.
- Allow JupyterHub overrides in the `qhub-config.yaml`.
- `qhub support` CLI option to save Kubernetes logs.
- Updates `conda-store` UI.

### What's Changed

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
- Disable/Remove the stale bot by @viniciusdc in https://github.com/Quansight/qhub/pull/923
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

### New Contributors

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

## Release 0.3.10 - May 6, 2021

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
