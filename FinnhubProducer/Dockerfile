# Use the official Miniconda3 image as the base image for the container
FROM continuumio/miniconda3

# Set the working directory inside the container to /app
WORKDIR /

COPY environment.yml environment.yml
COPY scripts scripts

# Create the conda environment using the environment.yml file
RUN conda env create -f environment.yml

# Set the default shell to use the conda environment 'finnhubDPL' and run subsequent commands within it
SHELL ["conda", "run", "--no-capture-output", "-n", "finnhubDPL", "/bin/bash", "-c"]

# Make the entry point script executable
RUN chmod +x scripts/entryPoint.sh

# Expose port 5004 to the outside world, allowing communication with the container
EXPOSE 5004

# Set the entry point of the container to the entry point script, which will execute the necessary startup tasks
ENTRYPOINT ["/scripts/entryPoint.sh"]
