# Use the official Miniconda3 image as the base image for the container
FROM continuumio/miniconda3

# Set the working directory inside the container to /app
WORKDIR /app

# Copy all files from the current directory to the container's /app directory
COPY ./ ./

# Copy the sample .env file to .env in the container's working directory
COPY sample.env .env

# Print the value of FINNHUB_API_KEY environment variable (for debugging purposes)
RUN echo $FINNHUB_API_KEY

# Replace the placeholder {{finnhub-api-key}} in the .env file with the actual value of FINNHUB_API_KEY environment variable
RUN sed -i 's/{{finnhub-api-key}}/$FINNHUB_API_KEY/g' .env

# Create the conda environment using the environment.yml file
RUN conda env create -f environment.yml

# Set the default shell to use the conda environment 'finnhubDPL' and run subsequent commands within it
SHELL ["conda", "run", "--no-capture-output", "-n", "finnhubDPL", "/bin/bash", "-c"]

# Make the entry point script executable
RUN chmod +x resources/scripts/entryPoint.sh

# Expose port 5004 to the outside world, allowing communication with the container
EXPOSE 5004

# Set the entry point of the container to the entry point script, which will execute the necessary startup tasks
ENTRYPOINT ["/app/resources/scripts/entryPoint.sh"]
