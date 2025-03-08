-- Create a keyspace
CREATE KEYSPACE IF NOT EXISTS market
WITH REPLICATION = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE market;

-- Create a table
CREATE TABLE IF NOT EXISTS shopping_cart (
    userid text PRIMARY KEY,
    item_count int,
    last_update_timestamp timestamp
);

-- Insert some data
INSERT INTO shopping_cart
(userid, item_count, last_update_timestamp)
VALUES ('9876', 2, toTimeStamp(now()));

INSERT INTO store.shopping_cart
(userid, item_count, last_update_timestamp)
VALUES ('1234', 5, toTimeStamp(now()));
