-- Create a keyspace
CREATE KEYSPACE IF NOT EXISTS market
WITH REPLICATION = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE market;

-- Create a table
CREATE TABLE IF NOT EXISTS market.shopping_cart (
    userid text PRIMARY KEY,
    item_count int,
    last_update_timestamp timestamp
);

CREATE TABLE IF NOT EXISTS market.stream_data (
    timebucket text,
    id uuid,
    last_updated timestamp,
    value double,
    PRIMARY KEY (timebucket, id)
) WITH CLUSTERING ORDER BY (id DESC);

-- Table for finnhub_trades data
-- CREATE TABLE IF NOT EXISTS market.finnhub_trade (
--     symbol TEXT,
--     event_timestamp BIGINT,
--     price DOUBLE,
--     PRIMARY KEY ((event_timestamp), symbol)
-- );

-- Table for finnhub_company_symbols data
-- CREATE TABLE IF NOT EXISTS market.finnhub_company_symbol (
--     event_timestamp BIGINT,
--     symbol TEXT,
--     PRIMARY KEY ((event_timestamp), symbol)
-- );

-- Table for STOCK_PRICES_1S data
CREATE TABLE IF NOT EXISTS market.stock_price_1s (
    partition_date DATE,
    event_timestamp BIGINT,
    processing_id UUID,
    insertion_timestamp BIGINT,
    symbol TEXT,
    count INT,
    avg_price DOUBLE,
    is_processed boolean,
    PRIMARY KEY ((partition_date), event_timestamp, processing_id, symbol)
);

-- Table for STOCK_SUMMARY data
CREATE TABLE IF NOT EXISTS market.stock_summary (
    partition_date DATE,
    event_timestamp BIGINT,
    processing_id UUID,
    insertion_timestamp BIGINT,
    total_price DOUBLE,
    symbols list<TEXT>,
    symbol_prices list<DOUBLE>,
    is_processed boolean,
    PRIMARY KEY ((partition_date), event_timestamp, processing_id)
);

-- Table for LATEST_PRICES data
CREATE TABLE IF NOT EXISTS market.latest_price (
    partition_date DATE,
    event_timestamp BIGINT,
    processing_id UUID,
    insertion_timestamp BIGINT,
    symbol TEXT,
    last_price DOUBLE,
    is_processed boolean,
    PRIMARY KEY ((partition_date), event_timestamp, processing_id, symbol)
);

-- Table for COMPANY_SYMBOLS data
CREATE TABLE IF NOT EXISTS market.company_symbol (
    symbol TEXT PRIMARY KEY
);
