# Use the official Miniconda3 image as the base image for this container.
# Miniconda is a lightweight distribution of Anaconda, which allows for managing Python environments and packages.
FROM continuumio/miniconda3

# Set the working directory in the container to /app.
WORKDIR /app

# Copy all files from the current directory on the host into the container's /app directory.
COPY ./ ./

# Copy the sample environment configuration file (sample.env) into the container as .env.
# This file may contain environment variable settings for the container.
COPY sample.env .env

# Create the Conda environment from the environment.yml file.
# This file typically defines all the required dependencies for the environment.
RUN conda env create -f environment.yml

# Make RUN commands use the newly created conda environment:
# By default, it uses the bash shell in the container.
# This shell will run inside the "finnhubDPL" conda environment and ensures that all commands are executed within that environment.
SHELL ["conda", "run", "--no-capture-output", "-n", "finnhubDPL", "/bin/bash", "-c"]

# Grant executable permissions to the entryPoint.sh script located in the 'resources/scripts' directory.
# This script will be used to start the application when the container runs.
RUN chmod +x resources/scripts/entryPoint.sh

# Expose port 5003 from the container.
# This makes the container's internal port 5003 accessible externally, allowing communication with the application.
EXPOSE 5003

# Specify the entrypoint for the container.
# When the container starts, it will execute the entryPoint.sh script located in /app/resources/scripts.
# This script will typically handle any setup or startup logic required before the main application (e.g., main.py) is run.
ENTRYPOINT ["/app/resources/scripts/entryPoint.sh"]
