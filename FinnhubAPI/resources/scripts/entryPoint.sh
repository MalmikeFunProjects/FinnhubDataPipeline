#!/bin/bash

# Activate the Poetry virtual environment
source .venv/bin/activate

cd /app

cp sample.env .env

# # Run FastAPI with host 0.0.0.0
# # Capture the exit code of the Python script to determine if it ran successfully or failed
# uvicorn main:app --host 0.0.0.0 --port 8000
python main.py
EXIT_CODE=$?

# # Check the exit code of the Python script
# # If the script completed successfully (exit code 0), log "SUCCESS"
# # If the script failed (any non-zero exit code), log "FAILURE"
if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS" > /tmp/healthcheck.log
else
    echo "FAILURE" > /tmp/healthcheck.log
fi

# The following line (which is commented out) would exit the script with the same exit code as the Python script.
# This ensures the container exits with the appropriate status if the Python script fails or succeeds.
# exit $EXIT_CODE

# Keep the container alive indefinitely by tailing /dev/null.
# This is useful for debugging purposes, as it keeps the container running.
# In a production environment, this line could be removed if you don't want the container to run indefinitely.
tail -f /dev/null
