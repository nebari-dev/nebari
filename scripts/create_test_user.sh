#!/bin/bash
TEST_USERNAME=$1
TEST_PASSWORD=$2
NEBARI_CONFIG_PATH=$3
count="$(nebari keycloak listusers --config "$NEBARI_CONFIG_PATH" | grep test-user | wc -l | tr -d '[:blank:]')"
echo "TEST_USERNAME: $TEST_USERNAME, TEST_PASSWORD: ${TEST_PASSWORD}"
cd
if [[ $count == "0" ]]; then
   nebari keycloak adduser \
   --user "${TEST_USERNAME}" "${TEST_PASSWORD}" \
   --config "$NEBARI_CONFIG_PATH"
else
  echo 'Nebari users already created.'
  echo `pwd`
  nebari keycloak listusers --config "$NEBARI_CONFIG_PATH"
fi
