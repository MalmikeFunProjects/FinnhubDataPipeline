FROM continuumio/miniconda3
WORKDIR /app
COPY ./ ./
COPY sample.env .env
RUN echo $FINNHUB_API_KEY
RUN sed -i 's/{{finnhub-api-key}}/$FINNHUB_API_KEY/g' .env
RUN conda env create -f environment.yml


# Make RUN commands use the new environment:
SHELL ["conda", "run", "--no-capture-output", "-n", "finnhubDPL", "/bin/bash", "-c"]

RUN chmod +x resources/scripts/entryPoint.sh

EXPOSE 5004
# The code to run when container is started:
# CMD ["conda", "run", "--no-capture-output", "-n", "finnhubDPL", "python3", "main.py"]
# Set entrypoint script
ENTRYPOINT ["/app/resources/scripts/entryPoint.sh"]
