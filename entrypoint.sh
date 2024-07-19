#!/bin/bash
# Activate the conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate geospatial_env

# Check if SCRIPT_TO_RUN is provided
if [ -z "$1" ]; then
    echo "Running container in interactive mode..."
    exec tail -f /dev/null
fi

# Check if the script exists in the container
if [ ! -f "$1" ]; then
    echo "Script $1 not found in /app directory. Exiting."
    exit 1
fi

# Execute the provided script with Python
echo "Running script: $1"
exec python "$1"

