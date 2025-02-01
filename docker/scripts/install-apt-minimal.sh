#!/usr/bin/env bash
# Copyright (c) Nebari Development Team.
# Distributed under the terms of the Modified BSD License.

apt-get update --fix-missing &&
    apt-get install -y wget bzip2 ca-certificates curl git &&
    apt-get clean &&
    rm -rf /var/lib/apt/lists/* /var/tmp/* /tmp/*
