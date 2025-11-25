### Drop all tables in keyspace called market
```bash
cqlsh -e "SELECT table_name FROM system_schema.tables where keyspace_name='market'" | grep -v table_name | awk '{if($1 ~ /^[a-zA-Z_]/) print "DROP TABLE market."$1";"}' | cqlsh
```
