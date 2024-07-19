#!/bin/bash

# Default values
IMAGE="geospatial_image"
DEFAULT_SCRIPT="default_script.sh"
SCRIPT_LOCATION="/app/geographical_division_handlers"

# Function to select script based on boundary_type
select_script() {
    local boundary_type=$1
    local data_file=$2
    local script_name=""
    local data_file_path=""
    local shape_file_path=""

    data_file_path="/data/$data_file"

    case $boundary_type in
        pincode)
            script_name="pincode_handler.py"
            shape_file_path="/app/INDIA_PINCODES/india_pincodes.shp"
            ;;
        district)
            script_name="district_handler.py"
            shape_file_path="/app/admin_boundaries_database/DISTRICT_BOUNDARY.shp"
            ;;
        state)
            script_name="state_handler.py"
            shape_file_path="/app/admin_boundaries_database/STATE_BOUNDARY.shp"
            ;;
        *)
            script_name=$DEFAULT_SCRIPT
            ;;
    esac

    echo "$script_name;$data_file_path;$shape_file_path"
}

# Parse arguments
boundary_type=$1
data_file=$2

# Select script to run based on boundary_type
script_info=$(select_script "$boundary_type" "$data_file")
IFS=';' read -r SCRIPT_TO_RUN DATA_FILE_PATH SHAPE_FILE_PATH <<< "$script_info"

# Run container
if [ -n "$boundary_type" ] && [ -n "$data_file" ]; then
    docker run -e DATA_FILE_PATH="$DATA_FILE_PATH" -e SHAPE_FILE_PATH="$SHAPE_FILE_PATH" -v /Users/sandeeppalo/Downloads:/data "$IMAGE" "$SCRIPT_LOCATION/$SCRIPT_TO_RUN"
else
    docker run -d "$IMAGE"
fi

# Output the status of the running container
echo "Container status:"
docker ps | grep "geospatial"
