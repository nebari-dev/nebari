#!/bin/bash

################################################################################
# Git Clone and/or Update Script
#
# This script automates Git repository handling with the following features:
#
# 1. Clones/Updates a Git repository into a specified folder;
# 2. Creates a `.firstrun` file in the folder to mark the script's execution, ensuring it only runs once for each folder.
#
# Usage: ./git_clone_update.sh "<folder1> <git_repo_url1>" [...]
#   - <folderX>: Path to the folder where the Git repository will be cloned or updated.
#   - <git_repo_urlX>: URL of the Git repository to clone or update.
################################################################################


# Check if at least one pair of folder and git repo URL is provided
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 \"<folder1> <git_repo_url1>\" \"<folder2> <git_repo_url2>\" ..."
  exit 1
fi

clone_update_repository() {
  # Clone or update a Git repository into a specified folder,
  # and create a `.firstrun` file to mark the script's execution.

  local folder_path="$1"
  local git_repo_url="$2"

  local firstrun_file="$folder_path/.firstrun"

  # Check if the .firstrun file exists
  if [ -f "$firstrun_file" ]; then
    echo "The script has already been run for $folder_path. Skipping. ✅"
  else
    if [ ! -d "$folder_path" ]; then
      mkdir -p "$folder_path"
    fi

    # Perform Git clone or update
    if [ -d "$folder_path/.git" ]; then
      echo "Updating Git repository in $folder_path"
      cd "$folder_path" || exit 1
      git pull
    else
      echo "Cloning Git repository to $folder_path"
      git clone "$git_repo_url" "$folder_path"
    fi

    touch "$firstrun_file"
  fi
}

# Iterate through pairs and run in parallel
for pair in "$@"; do
  read -r folder_path git_repo_url <<< "$pair"

  if [ -z "$folder_path" ] || [ -z "$git_repo_url" ]; then
    echo "Invalid argument format: \"$pair\". Please provide folder path and Git repository URL in the correct order."
  else
    clone_update_repository "$folder_path" "$git_repo_url" &
  fi
done

# Wait for all background processes to complete
wait

echo "All operations completed successfully. ✅"
