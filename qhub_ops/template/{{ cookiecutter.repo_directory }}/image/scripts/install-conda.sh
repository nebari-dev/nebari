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

apt-get autoremove --purge -y wget bzip2
apt-get clean
rm -rf /var/lib/apt/lists/*
