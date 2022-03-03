#!/usr/bin/env bash
set -euo pipefail
set -x

# === install conda environment ======
/opt/conda/condabin/mamba env create --prefix=/opt/conda/envs/default -f "${1}"

# ========= list dependencies ========
/opt/conda/condabin/mamba list -p /opt/conda/envs/default

# ========== cleanup conda ===========
/opt/conda/bin/mamba clean -afy
find /opt/conda/ -follow -type f -name '*.a' -delete
find /opt/conda/ -follow -type f -name '*.js.map' -delete
