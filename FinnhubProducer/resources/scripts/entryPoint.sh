#!/bin/bash

# Initialize Conda
# This command ensures that the Conda environment is correctly initialized and ready for use.
eval "$(conda shell.bash hook)"

# Activate the Conda environment
# Activates the Conda environment named 'finnhubDPL', setting up the appropriate environment for running the script.
conda activate finnhubDPL

# Run the Python script and capture the exit code
# Executes the Python script 'finnhub_producer.py' in the activated environment.
# The exit code of the script is captured to determine whether it ran successfully or failed.
python finnhub_producer.py
EXIT_CODE=$?

# Log success or failure
# Based on the exit code from the Python script, a success or failure message is written to a log file.
# If the exit code is 0 (indicating success), 'SUCCESS' is logged. Otherwise, 'FAILURE' is logged.
if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS" > /tmp/healthcheck.log  # Log success message
else
    echo "FAILURE" > /tmp/healthcheck.log  # Log failure message
fi

# Exit with the same exit code as the script
# The script is commented out here, but if uncommented, it would ensure that the container exits with the
# same exit code as the Python script, allowing proper reporting of success or failure to container orchestration systems.
# exit $EXIT_CODE

# Keep container alive (useful for debugging)
# This command is useful during debugging or testing, as it keeps the container running after the script completes.
# This is often used to keep the container alive when you want to inspect logs or run additional commands manually.
tail -f /dev/null
