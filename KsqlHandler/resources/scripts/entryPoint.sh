#!/bin/bash

# Initialize Conda
# This initializes Conda's shell environment. It allows us to use conda commands and activate environments within the script.
eval "$(conda shell.bash hook)"

# Activate the Conda environment
# Activates the Conda environment named 'finnhubDPL', which should have all necessary dependencies installed.
conda activate finnhubDPL

# Run the Python script and capture the exit code
# Executes the main Python script (main.py), which is the entry point for the application.
# The exit code of the script (i.e., success or failure) is captured in the EXIT_CODE variable.
python main.py
EXIT_CODE=$?

# Log success or failure
# After running the Python script, this conditional checks whether the exit code indicates success or failure.
# It writes either "SUCCESS" or "FAILURE" to a log file located at /tmp/healthcheck.log.
if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS" > /tmp/healthcheck.log
else
    echo "FAILURE" > /tmp/healthcheck.log
fi

# Exit with the same exit code as the script
# The script will exit with the same exit code as the Python script to indicate whether it ran successfully or not.
# If uncommented, this line would make the bash script exit with the same status as the Python script.
# exit $EXIT_CODE

# Keep container alive (useful for debugging)
# This command keeps the Docker container running indefinitely by following (tailing) /dev/null.
# It is helpful when debugging, as it prevents the container from exiting immediately after the script runs.
tail -f /dev/null
