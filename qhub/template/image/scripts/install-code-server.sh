#!/usr/bin/env bash
set -xe
DEFAULT_PREFIX="${1}"; shift # path to environment yaml or lock file

mkdir -p ${DEFAULT_PREFIX}/share/code-server
cd ${DEFAULT_PREFIX}/share/code-server

# Fetch the snapshot of https://code-server.dev/install.sh as of the time of writing
wget --quiet https://raw.githubusercontent.com/coder/code-server/326a1d1862872955cec062030df2bd103799a1eb/install.sh
expected_sum=ed18563871beb535130019b6c5b62206cc4a60c8bf4256aae96ce737951fc253

if [[ ! $(sha256sum install.sh) == "${expected_sum}  install.sh" ]];then
    echo Unexpected hash from code-server install script
    exit 1
fi

export VSCODE_EXTENSIONS="~/.local/share/code-server/extensions"

sh ./install.sh --method standalone --prefix ${DEFAULT_PREFIX}/share/code-server

export PATH="${DEFAULT_PREFIX}/share/code-server/bin:$PATH"

# Directly check whether the code-server call also works inside of conda-build
code-server --help

# Remove unnecessary resources
find ${DEFAULT_PREFIX}/share/code-server -name '*.map' -delete
rm -rf \
  ${DEFAULT_PREFIX}/share/code-server/node \
  ${DEFAULT_PREFIX}/share/code-server/lib/node \
  ${DEFAULT_PREFIX}/share/code-server/lib/lib* \
  ${DEFAULT_PREFIX}/share/code-server/lib/vscode/node_modules/vscode-sqlite3/build/Release/obj* \
  ${DEFAULT_PREFIX}/share/code-server/lib/vscode/node_modules/vscode-sqlite3/build/Release/sqlite3.a \
  ${DEFAULT_PREFIX}/share/code-server/lib/vscode/node_modules/vscode-sqlite3/deps \
  ${DEFAULT_PREFIX}/share/code-server/lib/vscode/node_modules/.cache \
  ${DEFAULT_PREFIX}/share/code-server/lib/vscode/out/vs/workbench/*.map \
  ${DEFAULT_PREFIX}/share/code-server/lib/vscode/node_modules/@coder/requirefs/coverage
find ${DEFAULT_PREFIX}/share/code-server/ -name obj.target | xargs rm -r

# Install the VS code proxy
pip install git+https://github.com/betatim/vscode-binder
