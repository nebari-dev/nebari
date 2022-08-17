# CLI current state


## Explicit goal(s)

To get a better understanding of how the QHub/Nebari CLI currently works, we will attempt to document the internal function calls and dependencies. When the time comes to design the new CLI, we will be able to make more informed decisions about what will need to change and what affects they might have.

As part of this work, we will also try to document any third-party dependencies. In the future, we would like to regularly update and test upstream changes. This will hopefully allow us to stop reacting to these changes and instead be proactive about if and when we need to make specific upgrades.

Lastly, as a stretch goal, it would be wonderful if we could help ourselves as developers by embedding useful dev-specific tools into the new CLI design. In order to do so, we should capture the shims and workarounds currently in place.


## CLI function calls

>NOTE: We are currently using Python standard library `argparse`.

### `qhub --help` / `qhub --version`

Function calls:
1. `qhub/cli/__init__.py:cli`


### `qhub init`

Function calls:
1. `qhub/cli/__init__.py:cli`
2. `qhub/cli/initialize.py:create_init_subcommand`
3. `qhub/cli/initialize.py:handle_init`
   - args
     - project
     - namespace
     - domain
     - platform
     - ci_provider
     - repository
     - repository_auto_provision
     - auth_provider
     - auth_auto_provider
     - terraform_state
     - kubernetes_version
     - disable_prompt
     - ssl_cert_email
   - dev mode
     - `QHUB_IMAGE_TAG`
     - `QHUB_DASK_TAG`
4. `qhub/initialize.py:render_config`
   - user `input` required here:
     - project_name
     - qhub_domain
     - auth provider - github client id
     - auth provider - github client secret
     - cloud provider - gcp PROJECT_ID
   - imported modules/functions from `qhub/provider`
     - `git`
       - `is_git_repo`
       - `initialize_git`
       - `add_git_remote`
     - `github`
       - `get_repository`
       - `create_repository`
       - `update_secret`
     - `oauth.auth0.create_client`
   - imported functions from `qhub/utils`
     - `set_docker_image_tag`
     - `set_qhub_dask_version`
     - `set_kubernetes_version`
   - other used functions
     - `github_auto_provision`
     - `github_repository_initialize`
     - `auth0_auto_provision`


### `qhub render`

Function calls:
1. `qhub/cli/__init__.py:cli`
2. `qhub/cli/render.py:create_render_subcommand`
3. `qhub/cli/render.py:handle_render`
   - args
     - config
     - dry-run
   - dev mode
     - QHUB_GH_BRANCH
4. `qhub/schema.py:verify`
   - relies on `Main` validator to verify config file is in the proper format
5. `qhub/render.py:render_template`
6. `qhub/render.py:render_contents`
7. `qhub/stages/tf_objects.py:stage_XX_...`

### `qhub validate`

Function calls:
1. `qhub/cli/__init__.py:cli`
2. `qhub/cli/render.py:create_validate_subcommand`
3. `qhub/cli/validate.py:handle_validate`
  - args
      - config
4. `qhub/utils.py:load_yaml`
  - Return yaml dict containing config loaded from config_filename.
5. `qhub/provider/cicd/linter.py:comment_on_pr`
6. `qhub/schema.py:verify`

### `qhub deploy`

Function calls:
1. `qhub/cli/__init__.py:cli`
2. `qhub/cli/deploy.py:create_deploy_subcommand`
  - flags:
      - --dns-provider
      - --skip-remote-state-provision
      - --dns-auto-provision
      - --disable-prompt
      - --diable-render
3. `qhub/cli/deploy.py:handle_deploy`
  - args
    - config
4. `qhub/schema.py:verify`
5. `qhub/utils.py:load_yaml`
  - Return yaml dict containing config loaded from config_filename.
6. `qhub/render.py:render_template`
7. `qhub/deploy.py:deploy_configuration`

### `qhub-destroy`

Function calls:
1. `qhub/cli/__init__.py:cli`
2. `qhub/cli/destroy.py:create_destroy_subcommand`
  - args
    - --disable-render
3. `qhub/cli/destroy.py:handle_destroy`
4. `qhub/schema.py:verify`
5. `qhub/utils.py:load_yaml`
6. `qhub/render.py:render_template`
7. `qhub/destroy.py:destroy_configuration`


### `qhub-keycloak`

Function calls:
1. `qhub/cli/__init__.py:cli`
2. `qhub/cli/keycloak.py:create_keycloak_subcommand`
  - argument:
    - keycloak_action
3. `qhub/cli/keycloak.py:handle_keycloak`
  - args:
    - config
4. `qhub/keycloak.py:do_keycloak`
5. `qhub/schema.py:verify`
6. `qhub/utils.py:load_yaml`


### `qhub-support`

Function calls:
1. `qhub/cli/__init__.py:cli`
2. `qhub/cli/support.py:create_support_subcommand`
  - args
    - QHUB_SUPPORT_LOG_FILE
3. `qhub/cli/support.py:handle_support`
  - args
    - config
    - v1
    - namespace
    - pods
4. `qhub/cli/support.py:get_config_namespace`
  - args:
    - path
    - zipfile
    - yaml
    - client
    - config

### `qhub-upgrade`

Function calls:
1. `qhub/cli/__init__.py:cli`
2. `qhub/cli/upgrade.py:create_upgrade_subcommand`
  - arguments:
    - --attempt-fixes
3. `qhub/cli/upgrade.py:handle_upgrade`
  - args
    - config_filename
    - pathlib
4. `qhub/upgrade.py:do_upgrade`
5. `qhub/schema.py:verify`
6. `qhub/utils.py:load_yaml`
7. `qhub/version.py:start_version`

### `qhub-cost`

Function calls:
1. `qhub/cli/__init__.py:cli`
2. `qhub/cli/cost.py:create_cost_subcommand`
  - arguments
    - -p
    - -d
    - -f
    - -c
    - -cc
3. `qhub/cli/cost.py:handle_cost_report`
  - args
    - path
    - dashboard
    - file
    - currency
    - compare
4. `qhub/cost.py:infracost_report`
  -  Generate a report of the infracost cost of the given path
    - args:
        - path: path to the qhub stages directory.