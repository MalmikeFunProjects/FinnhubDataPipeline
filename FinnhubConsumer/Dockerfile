# Use the Miniconda3 base image to provide a minimal Conda environment
FROM continuumio/miniconda3

# Set the working directory inside the container to /app
WORKDIR /app

# Copy the current directory content (the application) into the working directory in the container
COPY ./ ./

# Copy the environment file for setting up dependencies (e.g., libraries, tools)
COPY sample.env .env

# Create a Conda environment from the environment.yml file
# This will install necessary dependencies specified in the environment.yml
RUN conda env create -f environment.yml

# Set the default shell to use the Conda environment, to ensure that any subsequent RUN commands use the correct environment
# The `finnhubDPL` is the name of the environment that was created in the previous step.
SHELL ["conda", "run", "--no-capture-output", "-n", "finnhubDPL", "/bin/bash", "-c"]

# Ensure the entry point script is executable
RUN chmod +x resources/scripts/entryPoint.sh

# Expose port 5005 to allow external access to the application (typically for web apps or APIs)
EXPOSE 5005

# Specify the default command to run when the container starts.
# This line is currently commented out, but would start the application (main.py) if needed.
# CMD ["conda", "run", "--no-capture-output", "-n", "finnhubDPL", "python3", "main.py"]

# Set the entry point for the container to use the provided shell script
ENTRYPOINT ["/app/resources/scripts/entryPoint.sh"]
