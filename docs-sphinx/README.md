# Nebari CLI documentation

The CLI docs are generated using Sphinx and the sphinx-click extension. Although
a full Sphinx website is required in order to generate the docs, only the
`cli.html` file is used. This file gets copied over to the nebari-docs repo via
a GitHub Action.

The rich markup is currently unsupported by `sphinx-click` which means that the
color additions to the CLI get explicitly written in the docs
(https://github.com/ewels/rich-click/issues/48).

## Automation via GitHub Actions

_Generating the CLI HTML file_

A GitHub Action will run with every push to either the `dev` or `main` branches
which generates the documentation. A full Sphinx site build is required. To
build the site, go to the `docs-sphinx` folder and run

`make html`

The Action will then checks to see if `cli.html` (the generated doc) has
changed. If it has changed, it will open a new PR with an updated version.

_Updating the Nebari Docs repo_

The Nebari Documentation lives in a separate repo from the code itself
(https://github.com/nebari-dev/nebari-docs). A separate GitHub Action watches
for changes to the `cli.html` file in _this_ repo, and keeps it in sync with
the `cli.html` file in the docs repo.
