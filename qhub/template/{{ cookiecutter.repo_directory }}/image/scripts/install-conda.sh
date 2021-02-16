#!/usr/bin/env bash
set -xe

# Requires environment CONDA_VERSION
CONDA_VERSION=4.9.2-5

wget --no-hsts --quiet https://github.com/conda-forge/miniforge/releases/download/${CONDA_VERSION}/Miniforge3-${CONDA_VERSION}-Linux-x86_64.sh
wget --no-hsts --quiet https://github.com/conda-forge/miniforge/releases/download/${CONDA_VERSION}/Miniforge3-${CONDA_VERSION}-Linux-x86_64.sh.sha256 -O miniforge.checksum

if [ $(sha256sum -c miniforge.checksum | awk '{print $2}') != "OK" ]; then
   exit 1;
fi

mv Miniforge3-${CONDA_VERSION}-Linux-x86_64.sh miniforge.sh
sh ./miniforge.sh -b -p /opt/conda
rm miniforge.sh miniforge.checksum

ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh
echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
echo "conda activate base" >> ~/.bashrc

mkdir -p /etc/conda
cp /opt/scripts/condarc /etc/conda/condarc
