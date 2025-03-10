import datetime
import os
os.environ['CQLENG_ALLOW_SCHEMA_MANAGEMENT'] = '1'
import logging
import asyncio

from cassandra_client.connect import CassandraClient, CassandraConfig
from cassandra_client.models import ShoppingCart, StreamData

logging.basicConfig(level=logging.INFO)

async def generate_stream():
    for i in range(1000):
        yield i * 0.05
        await asyncio.sleep(0.05)

async def main():
    config = CassandraConfig(
        hosts=["cassandra"],
        port=9042,
        keyspace="market",
        # Adding retry configuration for more resilient connections
        retry_attempts=5,
        retry_delay=3
    )

    # Ensure the table schema is synchronized before writing data
    with CassandraClient(config) as setup_client:
        setup_client.sync_table(StreamData)
        logging.info("StreamData table schema synchronized")

    with CassandraClient(config) as client:
        batch_counter = 0
        current_bucket = StreamData.generate_timebucket()

        try:
            start_time = datetime.datetime.now()

            async for data_point in generate_stream():
                # Check if we neeed a new time bucket
                now = datetime.datetime.now()
                new_bucket = StreamData.generate_timebucket(now)
                if new_bucket != current_bucket:
                    # Force commit the current batch before changing buckets
                    if batch_counter > 0:
                        client.clear_batch(add_batch_data=True)
                        batch_counter = 0
                    current_bucket = new_bucket
                    logging.info(f"Switched to new time bucket: {current_bucket}")

                # Prepare data with time bucket
                data = {
                    "timebucket": current_bucket,
                    "last_updated": now,
                    "value": data_point
                }
                # Add to batch
                client.add_batch_data(batch_size=100, CustomModel=StreamData, data=data)
                batch_counter += 1

                # log progress periodically
                if batch_counter % 100 == 0:
                    elapsed = (datetime.datetime.now() - start_time).total_seconds()
                    rate = batch_counter / elapsed if elapsed > 0 else 0
                    logging.info(f"Processed {batch_counter} records at {rate:.2f} records/sec")

            # Make sure to flush any remaining batch items
            if batch_counter > 0:
                client.clear_batch(add_batch_data=True)
                logging.info(f"Final batch of {batch_counter % 100} records commited")

             # Get most recent data points
            recent_data = client.execute_query(
                "SELECT * FROM market.stream_data WHERE timebucket = %s LIMIT 10",
                [current_bucket]
            )

            logging.info(f"Recent data sample: {list(recent_data)}")

        except Exception as e:
            logging.error(f"Error processing stream: {e}")
            # Make sure to commit any partial batch on error
            if batch_counter > 0:
                try:
                    client.clear_batch(add_batch_data=True)
                except Exception as batch_e:
                    logging.error(f"Failed to commit final batch: {batch_e}")
            raise e


    with CassandraClient(config) as cluster:
        try:
            cluster.sync_table(ShoppingCart)

            shoppingCart = cluster.add_data_using_model(ShoppingCart, {
                'userid': '8932',
                'item_count': 4
            })

            logging.info(f"Shopping cart created: {shoppingCart}")

            retrieve_shopping_cart = cluster.get_item_by_key_data(ShoppingCart, {
                'userid': '8932'
            })
            logging.info(f"Retrieved shopping cart: {retrieve_shopping_cart}")

            all_records = cluster.get_all_items_by_model(ShoppingCart)
            for record in all_records:
                logging.info(f"UserID: {record.userid}, Item Count: {record.item_count}, Last Updated: {record.last_updated}")

        except Exception as e:
            raise e

if __name__ == "__main__":
    asyncio.run(main())
