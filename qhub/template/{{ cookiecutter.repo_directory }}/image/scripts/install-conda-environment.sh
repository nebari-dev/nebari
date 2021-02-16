#!/usr/bin/env bash
set -xe

CONDA_DIR = /opt/conda

# Assumes conda environment to install in argument "$1"

# ==== install conda dependencies ====
conda env update -f $1

# ========= list dependencies ========
conda list

# ========== cleanup conda ===========
conda clean -afy
# remove unnecissary files (statis, js.maps)
find ${CONDA_DIR} -follow -type f -name '*.a' -delete
find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete
find ${CONDA_DIR} -follow -type f -name '*.pyc' -delete

# Remove the pip cache created as part of installing miniconda
rm -rf /root/.cache
