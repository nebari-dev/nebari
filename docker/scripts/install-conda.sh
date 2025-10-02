#!/usr/bin/env bash
# Copyright (c) Nebari Development Team.
# Distributed under the terms of the Modified BSD License.

set -xe

# Requires environment MAMBAFORGE_SHA256, MINIFORGE_VERSION, and DEFAULT_ENV
arch=$(uname -i)
wget --quiet -O mambaforge.sh https://github.com/conda-forge/miniforge/releases/download/$MAMBAFORGE_VERSION/Mambaforge-Linux-$arch.sh

if [[ $arch == "aarch64" ]]; then
  echo "${MAMBAFORGE_AARCH64_SHA256} mambaforge.sh" >mambaforge.checksum
elif [[ $arch == "x86_64" ]]; then
  echo "${MAMBAFORGE_X86_64_SHA256} mambaforge.sh" >mambaforge.checksum
else
  echo "Unsupported architecture: $arch"
  exit 1
fi

echo $(sha256sum -c mambaforge.checksum)

if [ $(sha256sum -c mambaforge.checksum | awk '{print $2}') != "OK" ]; then
  echo Error when testing checksum
  exit 1
fi

# Install Mamba and clean-up
if [ -d "/opt/conda" ]; then
  sh ./mambaforge.sh -b -u -p /opt/conda
else
  sh ./mambaforge.sh -b -p /opt/conda
fi

rm mambaforge.sh mambaforge.checksum

mamba --version
mamba clean -afy

ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh

mkdir -p /etc/conda
cat <<EOF >/etc/conda/condarc
always_yes: true
changeps1: false
auto_update_conda: false
aggressive_update_packages: []
envs_dirs:
 - /home/conda/environments
EOF

# Fix permissions in accordance with jupyter stack permissions
# model
fix-permissions /opt/conda /etc/conda /etc/profile.d
