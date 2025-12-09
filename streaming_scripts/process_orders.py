from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql.streaming import *
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


input_schema = T.StructType([
    T.StructField("table", T.StringType(), True),
    T.StructField("action", T.StringType(), True),
    T.StructField("data", T.ArrayType(
        T.StructType([
            T.StructField("timestamp", T.TimestampType(), True),
            T.StructField("symbol", T.StringType(), True),
            T.StructField("bidSize", T.LongType(), True),
            T.StructField("bidPrice", T.DoubleType(), True),
            T.StructField("askPrice", T.DoubleType(), True),
            T.StructField("askSize", T.LongType(), True)
        ])
    ), True)
])

output_schema = T.StructType([
    T.StructField("symbol", T.StringType()),
    T.StructField("sellprice", T.DoubleType()),
    T.StructField("buyprice", T.DoubleType()),
    T.StructField("currenttimestamp", T.TimestampType())
])

spark = (SparkSession
        .builder
        .appName("Spark Kafka Streaming transformations")
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,com.datastax.spark:spark-cassandra-connector_2.12:3.2.0")
        .config("spark.cassandra.connection.host", "cassandra")
        .getOrCreate())

kafka_bootstrap_servers = "kafka:9092"
input_topic_name = "orders"

df = (spark
    .readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
    .option("subscribe", input_topic_name)
    .option("startingOffsets", "earliest")
    .option("failOnDataLoss", "false")
    .load())

df_transformed = (df
                    .select(
                        F.from_json(
                            F.col("value").cast(T.StringType()),
                            schema=input_schema
                        ).alias("msg")
                    ).select(
                        F.explode("msg.data").alias("data")
                    ).withColumn(
                        "timestamp_to_sec",
                        F.col("data.timestamp") + F.expr("INTERVAL 2 HOURS")
                    ).select(
                        F.col("timestamp_to_sec").alias("currenttimestamp"),
                        F.col("data.symbol"),
                        F.col("data.askPrice").alias("sellprice"),  # askPrice = sell price (ціна продажу)
                        F.col("data.bidPrice").alias("buyprice")    # bidPrice = buy price (ціна покупки)
                    ).withColumn("value", F.to_json(F.struct("*"))
                    ).select(
                        F.from_json(
                            F.col("value").cast(T.StringType()),
                            schema=output_schema
                        ).alias("data")
                    ).select("data.*"))

def process_batch(batch_df, batch_id):
    """Обробка кожного batch даних з логуванням"""
    try:
        row_count = batch_df.count()
        logger.info(f"Processing batch {batch_id} with {row_count} rows")
        
        if row_count > 0:
            # Показуємо приклад даних
            logger.info("Sample data from batch:")
            batch_df.show(5, truncate=False)
            
            # Записуємо в Cassandra
            batch_df.write \
                .format("org.apache.spark.sql.cassandra") \
                .mode("append") \
                .option("keyspace", "orders") \
                .option("table", "current_price") \
                .save()
            
            logger.info(f"Successfully wrote {row_count} rows to Cassandra")
        else:
            logger.warning(f"Batch {batch_id} is empty - no data to write")
    except Exception as e:
        logger.error(f"Error processing batch {batch_id}: {str(e)}", exc_info=True)
        raise

logger.info("Starting streaming query to Cassandra...")
logger.info("Waiting for data from Kafka topic 'orders'...")

query = (df_transformed.writeStream
    .foreachBatch(process_batch)
    .option("checkpointLocation", "/tmp/orders_checkpoint")
    .outputMode("update")
    .trigger(processingTime='10 seconds')
    .start())

query.awaitTermination()