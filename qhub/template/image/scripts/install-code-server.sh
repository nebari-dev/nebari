#!/usr/bin/env bash
set -xe

mkdir -p /opt/conda/envs/${DEFAULT_ENV}/share/code-server
cd /opt/conda/envs/${DEFAULT_ENV}/share/code-server

# Fetch the snapshot of https://code-server.dev/install.sh as of the time of writing
curl -fsSL https://raw.githubusercontent.com/coder/code-server/326a1d1862872955cec062030df2bd103799a1eb/install.sh > install.sh
expected_sum=ed18563871beb535130019b6c5b62206cc4a60c8bf4256aae96ce737951fc253

if [[ ! $(sha256sum install.sh) == "${expected_sum}  install.sh" ]];then
    echo Unexpected hash from code-server install script
    exit 1
fi

sh install.sh --prefix "/opt/conda/envs/${DEFAULT_ENV}/share/code-server"

# Install the VS code proxy
pip install git+https://github.com/betatim/vscode-binder