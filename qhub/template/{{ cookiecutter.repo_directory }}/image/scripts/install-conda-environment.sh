#!/usr/bin/env bash
set -xe

# Assumes conda packages to install in argument "$1"

# ==== install conda dependencies ====
/opt/conda/bin/conda env update -f $1

# ========= list dependencies ========
/opt/conda/bin/conda list

# ========== cleanup conda ===========
/opt/conda/bin/conda clean -afy
# remove unnecissary files (statis, js.maps)
find /opt/conda/ -follow -type f -name '*.a' -delete
find /opt/conda/ -follow -type f -name '*.js.map' -delete
