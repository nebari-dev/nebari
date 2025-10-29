#!/usr/bin/env bash
# Copyright (c) Nebari Development Team.
# Distributed under the terms of the Modified BSD License.

set -xe
DEFAULT_PREFIX="${1}"
shift # path to environment yaml or lock file
CODE_SERVER_VERSION=4.23.1

mkdir -p ${DEFAULT_PREFIX}/code-server
cd ${DEFAULT_PREFIX}/code-server

# Fetch the snapshot of https://code-server.dev/install.sh as of the time of writing
wget --quiet https://raw.githubusercontent.com/coder/code-server/v4.23.1/install.sh
expected_sum=ef0324043bc7493989764315e22bbc85c38c4e895549538b7e701948b64495e6

if [[ ! $(sha256sum install.sh) == "${expected_sum}  install.sh" ]]; then
    echo Unexpected hash from code-server install script
    exit 1
fi

mkdir /opt/tmpdir
sh ./install.sh --method standalone --prefix /opt/tmpdir --version ${CODE_SERVER_VERSION}

mv /opt/tmpdir/lib/code-server-${CODE_SERVER_VERSION}/* ${DEFAULT_PREFIX}/code-server
rm -rf /opt/tmpdir
