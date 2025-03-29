#!/usr/bin/env bash
# Copyright (c) Nebari Development Team.
# Distributed under the terms of the Modified BSD License.

set -xe

# Assumes apt packages installs packages in "$1" argument

# ====== install apt packages ========
apt-get update
apt-get install -y --no-install-recommends $(grep -vE "^\s*#" $1 | tr "\n" " ")

# ========== cleanup apt =============
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
