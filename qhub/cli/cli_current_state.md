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

...

### `qhub validate`
