#!/usr/bin/env bash
# Copyright (c) Nebari Development Team.
# Distributed under the terms of the Modified BSD License.

set -xe

# Adding the packagecloud repository for git-lfs installation
wget --quiet -O script.deb.sh https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh
expected_sum=8c4d07257b8fb6d612b6085f68ad33c34567b00d0e4b29ed784b2a85380f727b

if [[ ! $(sha256sum script.deb.sh) == "${expected_sum}  script.deb.sh" ]]; then
    echo Unexpected hash from git-lfs install script
    exit 1
fi

# Install packagecloud's repository signing key and add repository to apt
bash ./script.deb.sh

# Install git-lfs
apt-get install -y --no-install-recommends git-lfs
