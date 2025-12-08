from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.sql.streaming import *


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
                        F.col("data.bidPrice").alias("sellprice"),
                        F.col("data.askPrice").alias("buyprice")
                    ).withColumn("value", F.to_json(F.struct("*"))
                    ).select(
                        F.from_json(
                            F.col("value").cast(T.StringType()),
                            schema=output_schema
                        ).alias("data")
                    ).select("data.*"))

(df_transformed.writeStream
    .format("org.apache.spark.sql.cassandra")
    .option("keyspace", "orders")
    .option("table", "current_price")
    .option("checkpointLocation", "/tmp/orders_checkpoint")
    .start()
    .awaitTermination())