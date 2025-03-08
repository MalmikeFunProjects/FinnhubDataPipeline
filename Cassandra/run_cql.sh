#!/bin/bash

# Wait for the Cassandra cluster to form
echo "Waiting for Cassandra cluster to be ready..."
sleep 30  # Initial wait for cluster to start forming

# Keep checking until all expected nodes are up
while true; do
    # Try to connect to the seed node
    if ! nc -z cassandra-seed 9042; then
        echo "Cannot connect to cassandra-seed yet. Waiting..."
        sleep 10
        continue
    fi

    # Check node status
    node_count=$(nodetool -h cassandra-seed status | grep -c "UN")
    echo "Current healthy nodes: $node_count/3"

    # We expect 3 nodes total (1 seed + 2 regular nodes)
    if [[ "$node_count" -eq 3 ]]; then
        echo "All Cassandra nodes are up and running!"
        break
    fi

    echo "Waiting for all Cassandra nodes to join the cluster..."
    sleep 10
done

# Allow some time for schema propagation
echo "Allowing time for schema propagation..."
sleep 10

# Run the initialization CQL
echo "Initializing database schema..."
cqlsh cassandra-seed -f /app/init.cql

echo "Initialization complete!"
