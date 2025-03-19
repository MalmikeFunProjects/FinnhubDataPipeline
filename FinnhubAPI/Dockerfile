# Use the official Python 3.12 slim image as base
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /

# Insatll system dependencies needed for poetry and project
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https:/install.python-poetry.org | POETRY_HOME=/etc/poetry python3 -

# Add Poetry's bin directory to the PATH environment variable
ENV PATH="/etc/poetry/bin:$PATH"

RUN which poetry

# Copy project files
COPY pyproject.toml ./
COPY resources ./resources

# Configure Poetry to create virtualenvs in the project directory
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# RUN which curl

# # Install project dependencies using poetry
RUN poetry --no-interaction --no-ansi --no-root install

# # Ensure the entry point script is executable
RUN chmod +x resources/scripts/entryPoint.sh

# # Expose port 5005 to allow external access to the application (typically for web apps or APIs)
EXPOSE 8000

# Set the entry point for the container to use the provided shell script
ENTRYPOINT ["/resources/scripts/entryPoint.sh"]
