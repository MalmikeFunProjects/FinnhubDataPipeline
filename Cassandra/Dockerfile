FROM cassandra:latest

# Install netcat for connectivity checks
RUN apt-get update && apt-get install -y netcat && apt-get clean

WORKDIR /app
COPY init.cql .
COPY run_cql.sh .
RUN chmod +x /app/run_cql.sh

CMD ["/app/run_cql.sh"]
