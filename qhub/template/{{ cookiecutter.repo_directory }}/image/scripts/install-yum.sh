#!/usr/bin/env bash
set -xe

# Assumes apt packages installs packages in "$1" argument
# ====== install apt packages ========
yum update -y
yum install -y $(grep -vE "^\s*#" $1  | tr "\n" " ")

# ========== cleanup apt =============
yum clean all
rm -rf /tmp/* /var/tmp/*
rm -rf /var/cache/yum
