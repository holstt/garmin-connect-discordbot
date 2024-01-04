#!/bin/bash
# This script can be used to run the docker project in a prod environment, where the container is run as a dedicated user with restricted permissions

set -e
echo "Running script: $0"

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

# User that will be created (if not exist) and used for running the container
USERNAME="garmin-connect-bot"
# Location of .env and the creation of the container data directory is assumed to be placed directly in the project root directory
CONTAINER_DATA_DIR="$SCRIPT_DIR/../data"
ENV_PATH="$SCRIPT_DIR/../prod.env"
# Command to run the project
COMMAND="DOCKER_REPO_NAME=my-docker-repo docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"

"$SCRIPT_DIR"/docker_setup.sh "$USERNAME" "$CONTAINER_DATA_DIR" "$ENV_PATH" "$COMMAND"
