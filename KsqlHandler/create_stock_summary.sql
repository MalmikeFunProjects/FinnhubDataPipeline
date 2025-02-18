-- Set the auto offset reset configuration to start from the earliest available record in case of consumer reset.
SET 'auto.offset.reset'='earliest';

-- Create a stream named STOCK_PRICES for consuming stock price data from Kafka topic 'finnhub_trades'.
-- This stream contains the price, symbol, and timestamp fields.
CREATE STREAM STOCK_PRICES
(
    price DOUBLE,             -- Price of the stock
    symbol VARCHAR,           -- Stock symbol (ticker)
    timestamp BIGINT          -- Timestamp of the price entry (epoch time)
)
WITH
(
    KAFKA_TOPIC='finnhub_trades',    -- Kafka topic for incoming data
    VALUE_FORMAT='AVRO',             -- The format of the value in the Kafka topic (can be AVRO or JSON)
    TIMESTAMP='timestamp'            -- Specifies that the 'timestamp' field should be used for event time
);

-- Create a stream named SYMBOLS to get the latest stock symbols and their corresponding timestamp.
-- This stream consumes data from the 'finnhub_company_symbols' Kafka topic.
CREATE STREAM SYMBOLS
(
    SYMBOL VARCHAR,              -- The stock symbol (ticker)
    TIMESTAMP BIGINT             -- The timestamp of the symbol entry (epoch time)
)
WITH
(
    KAFKA_TOPIC = 'finnhub_company_symbols',  -- Kafka topic containing stock symbols
    VALUE_FORMAT = 'AVRO',                   -- Data format is AVRO
    TIMESTAMP = 'timestamp'                  -- Uses the timestamp field for event time
);

-- Create a table called COMPANY_SYMBOLS that stores the latest stock symbols,
-- pulling the latest available timestamp for each symbol.
CREATE TABLE COMPANY_SYMBOLS (
    KAFKA_TOPIC = 'COMPANY_SYMBOLS',      -- Kafka topic storing the company symbols
    VALUE_FORMAT = 'AVRO',                -- Value format is AVRO
    KEY_FORMAT = 'AVRO'                   -- Key format is AVRO, could be 'KAFKA' if keys are in a different format
) AS
SELECT
  SYMBOL,                               -- The stock symbol
  LATEST_BY_OFFSET(TIMESTAMP) AS MX      -- Latest timestamp for each symbol (determined by the latest offset)
FROM SYMBOLS
GROUP BY SYMBOL
EMIT CHANGES;                           -- Continuous stream of updates on the latest symbol information

-- Create a table called LATEST_PRICES that contains the most recent price for each stock symbol.
-- The table joins the STOCK_PRICES stream with the COMPANY_SYMBOLS table.
CREATE TABLE LATEST_PRICES (
    KAFKA_TOPIC = 'LATEST_PRICES',        -- Kafka topic where the latest stock prices are stored
    VALUE_FORMAT = 'AVRO',                -- Value format is AVRO
    KEY_FORMAT = 'AVRO'                   -- Key format is AVRO
) AS
SELECT
  sp.SYMBOL as SYMBOL,                   -- Stock symbol from STOCK_PRICES stream
  COALESCE(LATEST_BY_OFFSET(sp.price), CAST(0 AS DOUBLE)) AS LAST_PRICE,  -- Get the most recent price, default to 0 if no price is available
  LATEST_BY_OFFSET(sp.TIMESTAMP) AS TIMESTAMP  -- Get the most recent timestamp
FROM STOCK_PRICES sp
  LEFT JOIN COMPANY_SYMBOLS cs           -- Join with the COMPANY_SYMBOLS table to match stock symbols
  ON sp.SYMBOL = cs.SYMBOL
GROUP BY sp.SYMBOL
EMIT CHANGES;                            -- Continuously emit changes as new stock prices come in

----------------------------------------------

-- Create a table STOCK_PRICES_1S that aggregates stock prices over a 1-second tumbling window.
-- It calculates the count of entries and average price for each stock symbol per second.
CREATE TABLE STOCK_PRICES_1S (
    KAFKA_TOPIC = 'STOCK_PRICES_1S',      -- Kafka topic where aggregated stock prices per second are stored
    VALUE_FORMAT = 'AVRO',                -- Value format is AVRO
    KEY_FORMAT = 'AVRO'                   -- Key format is AVRO
) AS
SELECT
  SYMBOL,                               -- Stock symbol
  WINDOWSTART AS TIMESTAMP,             -- The start of the tumbling window (timestamp)
  COUNT(*) AS COUNT,                     -- The number of stock entries within the 1-second window
  AVG(PRICE) AS AVG_PRICE                -- The average stock price within the 1-second window
FROM STOCK_PRICES
WINDOW TUMBLING (SIZE 1 SECONDS)        -- Tumbling window of 1 second
GROUP BY SYMBOL
EMIT FINAL;                             -- Emit the final result for each tumbling window (once every second)

-- Create a stream STOCK_PRICES_1S_STREAM to output real-time data for stock prices within the 1-second tumbling window.
CREATE STREAM STOCK_PRICES_1S_STREAM
(
    SYMBOL VARCHAR KEY,                  -- Declare SYMBOL as the key for the stream
    AVG_PRICE DOUBLE,                         -- The price of the stock
    TIMESTAMP BIGINT                      -- The timestamp when the price is recorded
)
WITH
(
    KAFKA_TOPIC = 'STOCK_PRICES_1S',      -- Kafka topic where the data is stored
    VALUE_FORMAT = 'AVRO',                -- Value format is AVRO
    WINDOW_TYPE = 'TUMBLING',             -- Define the window type as 'TUMBLING' for periodic aggregation
    WINDOW_SIZE = '1 SECONDS'             -- Define the window size as 1 second
);

-- Create a table STOCK_SUMMARY that aggregates the total price and the list of stock symbols within each 1-second window.
-- This table sums the price and collects the symbols for each window.
CREATE TABLE STOCK_SUMMARY WITH (
    KAFKA_TOPIC = 'STOCK_SUMMARY',        -- Kafka topic where the stock summary is stored
    VALUE_FORMAT = 'AVRO',                -- Value format is AVRO
    KEY_FORMAT = 'AVRO'                   -- Key format is AVRO
) AS
SELECT
  TIMESTAMP,                            -- Timestamp of the aggregation window
  SUM(AVG_PRICE) AS TOTAL_PRICE,             -- Sum of stock prices within the window
  COLLECT_LIST(SYMBOL) AS symbols       -- Collect the list of symbols for each window
FROM stock_prices_1s_stream
WINDOW TUMBLING(SIZE 1 SECONDS)         -- Tumbling window of 1 second
GROUP BY TIMESTAMP
EMIT CHANGES;                           -- Continuously emit changes as new data comes in

-- The following query will return a continuous stream of stock summary data.
select * from STOCK_SUMMARY_STREAM emit changes;
