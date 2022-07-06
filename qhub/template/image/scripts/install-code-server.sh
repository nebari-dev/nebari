#!/usr/bin/env bash
set -xe
# DEFAULT_PREFIX="${1}"; shift # path to environment yaml or lock file

mkdir -p /opt/code-server
cd /opt/code-server

# Fetch the snapshot of https://code-server.dev/install.sh as of the time of writing
wget --quiet https://raw.githubusercontent.com/coder/code-server/326a1d1862872955cec062030df2bd103799a1eb/install.sh
expected_sum=ed18563871beb535130019b6c5b62206cc4a60c8bf4256aae96ce737951fc253

if [[ ! $(sha256sum install.sh) == "${expected_sum}  install.sh" ]];then
    echo Unexpected hash from code-server install script
    exit 1
fi

mkdir /opt/tmpdir
sh ./install.sh --method standalone --prefix /opt/tmpdir

mv /opt/tmpdir/lib/code-server-4.5.0/* /opt/code-server/
rm -rf /opt/tmpdir

cat <<'EOF' >opt/code-server/bin/code-server
#!/bin/bash
node opt/code-server/out/node/entry.js $*
EOF
