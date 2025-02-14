#!/bin/bash

# Show help if no arguments are passed
if [ $# -eq 0 ]; then
    echo "No options provided. Run '$0 -h' for usage information."
    exit 1
fi

# Define service groups
kafka_core=("zookeeper" "broker" "schema-registry" "ksqldb-server")
kafka_monitoring=("control-center" "kafka-rest" "ksqldb-cli")
application_services=("ksql-handler" "finnhub-producer" "finnhub-consumer")

while getopts ":s:br:hv" opt; do
    case $opt in
    r) run_services="$OPTARG" ;;
    s) stop_services="$OPTARG" ;;
    b) build="--build" ;;
    h)
        echo "Usage: $0 [-r <run_services>] [-s <stop_services>] [-b] [-h] [-v]"
        echo ""
        echo "Adding -b to -r states that the containers should rebuild"
        echo "Options for -r (run_services):"
        echo "  all_services:             Run all defined services."
        echo "  required_services:        Run only required services for the pipeline."
        echo "  kafka_core:               Run core Kafka services."
        echo "  kafka_monitoring:         Run Kafka monitoring services."
        echo "  application_services:     Run only application micro services."
        echo "Options for -s (stop_services):"
        echo "  all_services:             Stop all defined services."
        echo "  kafka_monitoring:         Stop Kafka monitoring services."
        echo "  application_services:     Stop application micro services."
        exit 0
        ;;
    v) verbose=true ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    :)
        echo "Option -$OPTARG requires an argument." >&2
        exit 1
        ;;
    esac
done

# Enable verbose mode if requested
[ "$verbose" = true ] && echo "Verbose mode enabled."

# Prevent using both -r and -s at the same time
if [ -n "$run_services" ] && [ -n "$stop_services" ]; then
    echo "Cannot use -r and -s together. Choose either run or stop."
    exit 1
fi

# Function to run services
run_services() {
    case "$1" in
    all_services)
        echo "Starting all services..."
        docker compose up $build -d
        ;;
    required_services)
        echo "Starting required services (Kafka core + application services)..."
        docker compose up $build -d "${kafka_core_services[@]}" "${application_services[@]}"
        ;;
    kafka_core | kafka_monitoring | application_services)
        eval "services=(\"\${${1}[@]}\")"
        echo "Starting $1..."
        docker compose up $build -d "${services[@]}"
        ;;
    *)
        echo "Invalid option for -r: $1"
        exit 1
        ;;
    esac
}

# Function to stop services
stop_services() {
    case "$1" in
    all_services)
        echo "Stopping all services..."
        docker compose down
        ;;
    kafka_monitoring | application_services)
        eval "services=(\"\${${1}[@]}\")"
        echo "Starting $1..."
        docker compose stop "${services[@]}"
        ;;
    *)
        echo "Invalid option for -s: $1"
        exit 1
        ;;
    esac
}

# Execute corresponding function
echo "$run_services"
[ -n "$run_services" ] && run_services "$run_services"
[ -n "$stop_services" ] && stop_services "$stop_services"
