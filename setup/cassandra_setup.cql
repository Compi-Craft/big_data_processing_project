CREATE KEYSPACE IF NOT EXISTS orders WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
CREATE KEYSPACE IF NOT EXISTS trades WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS orders.current_price (
    symbol TEXT PRIMARY KEY,
    sellprice DOUBLE,
    buyprice DOUBLE,
    currenttimestamp TIMESTAMP
);
