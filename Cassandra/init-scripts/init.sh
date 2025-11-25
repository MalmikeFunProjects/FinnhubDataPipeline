#!/bin/bash
set -e
echo 'Waiting for Cassandra to be ready...';
cqlsh cassandra -e 'SELECT now() FROM system.local';
echo 'Creating keyspace and tables...';
cqlsh cassandra -f /init-scripts/init.cql;
echo 'Initialization completed.'
touch /tmp/init-completed
