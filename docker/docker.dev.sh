#!/bin/bash
# The purpose of this script is being able to run and test the docker project in a dev environment

set -e
echo "Running script: $0"

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

# Location of .env and the creation of the container data directory is assumed to be in the _parent_ of the project root directory (avoids committing secrets to git by accident)
CONTAINER_DATA_DIR="$SCRIPT_DIR/../../data"
ENV_PATH="$SCRIPT_DIR/../../.env"

# Set container user to current user in dev
USERNAME=$(whoami)
GROUPNAME=$USERNAME

# Uncomment to use setup script used in prod (set up user, dir, permissions). May not be relevant/necessary in dev
# ./docker_setup.sh $CONTAINER_DATA_DIR $ENV_PATH $USERNAME $GROUPNAME
"$SCRIPT_DIR"/docker_run.sh "$CONTAINER_DATA_DIR" "$ENV_PATH" "$USERNAME" "$GROUPNAME"
