#!/usr/bin/env bash
set -xe
# Requires environment CONDA_SHA256, CONDA_VERSION, and DEFAULT_ENV
wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-$CONDA_VERSION-Linux-x86_64.sh

echo "${CONDA_SHA256}  Miniconda3-$CONDA_VERSION-Linux-x86_64.sh" > miniconda.checksum

if [ $(sha256sum -c miniconda.checksum | awk '{print $2}') != "OK" ]; then
   echo Error when testing checksum
   exit 1;
fi

mv Miniconda3-$CONDA_VERSION-Linux-x86_64.sh miniconda.sh
sh ./miniconda.sh -b -p /opt/conda
rm miniconda.sh miniconda.checksum

ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh

mkdir -p /etc/conda
cat <<EOF > /etc/conda/condarc
always_yes: true
changeps1: false
auto_update_conda: false
aggressive_update_packages: []
envs_dirs:
 - /home/conda/environments
 - /home/jovyan/.conda/envs
pkgs_dirs:
 - /home/jovyan/.conda/pkgs
EOF

# Fix permissions in accordance with jupyter stack permissions
# model
fix-permissions /opt/conda /etc/conda /etc/profile.d
