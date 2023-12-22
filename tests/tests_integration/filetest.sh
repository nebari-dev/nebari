#! /bin/bash

# Set the path to your YAML file
yaml_file="./nebari-config.yaml"

# Define expected values for each parameter
declare -A expected_values
expected_values["provider"]="do"
expected_values["namespace"]="dev"
expected_values["nebari_version"]="2023.11.1"
expected_values["project_name"]="nebari-test"
expected_values["ci_cd.type"]="none"
expected_values["terraform_state.type"]="remote"
expected_values["security.keycloak.initial_root_password"]="74nq7y3q9drifpnuby714rftirepddox"
expected_values["security.authentication.type"]="password"
expected_values["theme.jupyterhub.hub_title"]="Nebari - nebari-test"
expected_values["theme.jupyterhub.welcome"]="Welcome! Learn about Nebari's features and configurations in <a href=\"https://www.nebari.dev/docs/welcome\">the documentation</a>. If you have any questions or feedback, reach the team on <a href=\"https://www.nebari.dev/docs/community#getting-support\">Nebari's support forums</a>."
expected_values["theme.jupyterhub.hub_subtitle"]="Your open source data science platform, hosted on Digital Ocean"
expected_values["digital_ocean.kubernetes_version"]="1.26.9-do.0"
expected_values["digital_ocean.region"]="nyc3"

# Loop through each parameter and check its existence and value
for parameter_name in "${!expected_values[@]}"; do
    if yq eval ".${parameter_name}" "$yaml_file" > /dev/null 2>&1; then
        actual_value=$(yq eval ".${parameter_name}" "$yaml_file")
        expected_value="${expected_values[${parameter_name}]}"
        
        if [ "$actual_value" == "$expected_value" ]; then
            echo "Parameter '$parameter_name' has the expected value: $expected_value"
        else
            echo "Parameter '$parameter_name' has a different value."
            echo "Expected value: $expected_value"
            echo "Actual value: $actual_value"
        fi
    else
        echo "Parameter '$parameter_name' does not exist in the YAML file."
    fi
done