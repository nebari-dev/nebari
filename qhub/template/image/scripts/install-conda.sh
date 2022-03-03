#!/usr/bin/env bash
set -xe

CONDA_DIR=/opt/conda
MINIFORGE_NAME=Miniforge3
MINIFORGE_VERSION=4.11.0-4
TINI_VERSION=v0.18.0
TARGETPLATFORM=amd64

# install essentials for conda and tini
apt-get update > /dev/null
apt-get install --no-install-recommends --yes wget bzip2 ca-certificates git > /dev/null
apt-get clean
rm -rf /var/lib/apt/lists/*

# install tini
wget --no-hsts --quiet https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-${TARGETPLATFORM} -O /usr/local/bin/tini
chmod +x /usr/local/bin/tini

# install conda
wget --no-hsts --quiet https://github.com/conda-forge/miniforge/releases/download/${MINIFORGE_VERSION}/${MINIFORGE_NAME}-${MINIFORGE_VERSION}-Linux-$(uname -m).sh -O /tmp/miniforge.sh
/bin/bash /tmp/miniforge.sh -b -p ${CONDA_DIR}

# install mamba
conda install -y -c conda-forge mamba

# cleanup
rm /tmp/miniforge.sh
conda clean -tipsy
find ${CONDA_DIR} -follow -type f -name '*.a' -delete
find ${CONDA_DIR} -follow -type f -name '*.pyc' -delete
conda clean -afy

# minimal steps to have conda available
echo ". ${CONDA_DIR}/etc/profile.d/conda.sh && conda activate base" >> /etc/skel/.bashrc
echo ". ${CONDA_DIR}/etc/profile.d/conda.sh && conda activate base" >> ~/.bashrc
