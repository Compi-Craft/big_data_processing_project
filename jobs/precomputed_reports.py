from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum, count, expr
from datetime import datetime, timedelta
import pytz

spark = SparkSession.builder \
    .appName("AggregateTradesLastHour") \
    .getOrCreate()

db_url = "jdbc:postgresql://db:5432/authdb"
db_properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

historical_trades_df = spark.read.jdbc(
    url=db_url,
    table="historical_trades",
    properties=db_properties
)

historical_trades_df.show()
kyiv_tz = pytz.timezone("Europe/Kyiv")

now = datetime.now(kyiv_tz).replace(minute=0, second=0, microsecond=0).replace(tzinfo=None)
prev_hour = now - timedelta(hours=1)

filtered_df = historical_trades_df.filter(
    (col("currenttimestamp") >= prev_hour) & (col("currenttimestamp") < now)
)

aggregated_df = filtered_df.groupBy("symbol").agg(
    count("*").alias("transaction_count"),
    _sum("trade_volume").alias("total_trade_volume")
)

aggregated_df = aggregated_df.withColumn("hour_start", expr(f"TIMESTAMP('{prev_hour}')"))

aggregated_df.show()

aggregated_df.write.jdbc(
    url=db_url,
    table="symbol_stats_last_hour",
    mode="append",
    properties=db_properties
)

