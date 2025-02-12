#!/bin/bash

# Initialize Conda
eval "$(conda shell.bash hook)"

# Activate the Conda environment
conda activate finnhubDPL

# Run the Python script and capture the exit code
python main.py
EXIT_CODE=$?

# Log success or failure
if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS" > /tmp/healthcheck.log
else
    echo "FAILURE" > /tmp/healthcheck.log
fi

# Exit with the same exit code as the script
# exit $EXIT_CODE

# Keep container alive (useful for debugging)
tail -f /dev/null
