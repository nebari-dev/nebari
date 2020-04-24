#!/usr/bin/env bash
set -xe

# Requires environment CONDA_SHA256, CONDA_VERSION

apt-get update
apt-get install -y wget bzip2

wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-$CONDA_VERSION-Linux-x86_64.sh

echo "${CONDA_SHA256}  Miniconda3-$CONDA_VERSION-Linux-x86_64.sh" > miniconda.checksum

if [ $(sha256sum -c miniconda.checksum | awk '{print $2}') != "OK" ]; then
   exit 1;
fi

mv Miniconda3-$CONDA_VERSION-Linux-x86_64.sh miniconda.sh
sh ./miniconda.sh -b -p /opt/conda
rm miniconda.sh miniconda.checksum

ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh
echo ". /opt/conda/etc/profile.d/conda.sh" >> /etc/profile

mkdir -p /etc/conda
echo "always_yes: true" >> /etc/conda/.condarc
echo "changeps1: false" >> /etc/conda/.condarc
echo "auto_update_conda: false" >> /etc/conda/.condarc
echo "aggressive_update_packages: []" >> /etc/conda/.condarc

apt-get autoremove --purge -y wget bzip2
apt-get clean
rm -rf /var/lib/apt/lists/*
