#!/bin/bash
set -xe

echo "Installing Miniforge..."
echo ". ${CONDA_DIR}/etc/profile.d/conda.sh ; conda activate ${CONDA_ENV}" > etc/profile.d/init_conda.sh
URL="https://github.com/conda-forge/miniforge/releases/download/${CONDA_VERSION}/Miniforge3-${CONDA_VERSION}-Linux-x86_64.sh"
wget --quiet ${URL} -O miniconda.sh
/bin/bash miniconda.sh -u -b -p ${CONDA_DIR}
rm miniconda.sh
ln -s ${CONDA_DIR}/etc/profile.d/conda.sh /etc/profile.d/conda.sh
conda install -y -c conda-forge mamba
mamba clean -afy
find ${CONDA_DIR} -follow -type f -name '*.a' -delete
find ${CONDA_DIR} -follow -type f -name '*.pyc' -delete
echo "CONDA INSTALLED"
