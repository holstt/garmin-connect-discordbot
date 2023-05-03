#!/bin/bash
set -e
echo "Running script: $0"

# This script can be used to run the docker project in a production environment, where different paths may be used.
# Working dir is assumed to be in the docker folder of the project
# Location of .env and the creation of the container data directory is assumed to be placed directly in the project root directory

# Set paths with above assumptions
CONTAINER_DATA_DIR="../data"
ENV_PATH="../.env.prod"
USERNAME="garmin-health-bot"
GROUPNAME=$USERNAME


./docker_setup.sh $CONTAINER_DATA_DIR $ENV_PATH $USERNAME $GROUPNAME
./docker_run.sh $CONTAINER_DATA_DIR $ENV_PATH $USERNAME $GROUPNAME
