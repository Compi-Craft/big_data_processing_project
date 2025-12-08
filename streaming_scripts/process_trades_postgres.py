from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import pyspark.sql.types as T

inner_input_schema = T.StructType([
    T.StructField("timestamp", T.TimestampType(), True),
    T.StructField("symbol", T.StringType(), True),
    T.StructField("side", T.StringType(), True),
    T.StructField("size", T.IntegerType(), True),
    T.StructField("price", T.DoubleType(), True),
    T.StructField("tickDirection", T.StringType(), True),
    T.StructField("trdMatchID", T.StringType(), True),
    T.StructField("grossValue", T.LongType(), True),
    T.StructField("homeNotional", T.DoubleType(), True),
    T.StructField("foreignNotional", T.DoubleType(), True),
    T.StructField("trdType", T.StringType(), True)
])

input_schema = T.StructType([
    T.StructField("table", T.StringType(), True),
    T.StructField("action", T.StringType(), True),
    T.StructField("data", T.ArrayType(inner_input_schema), True)
])

spark = (SparkSession
        .builder
        .appName("Spark Kafka Streaming transformations")
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,org.postgresql:postgresql:42.2.18")
        .getOrCreate())

kafka_bootstrap_servers = "kafka:9092"
input_topic_name = "trades"

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
                        "currenttimestamp",
                        F.to_timestamp("data.timestamp") + F.expr("INTERVAL 2 HOURS")
                    ).select(
                        "currenttimestamp",
                        "data.symbol",
                        F.col("data.foreignNotional").alias("trade_volume"),
                        F.col("data.trdMatchID").alias("trade_id")
                    ))

pg_url = "jdbc:postgresql://db:5432/authdb"
pg_properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

def write_to_postgres(batch_df, batch_id):
    batch_df.write.jdbc(url=pg_url,
                        table="public.historical_trades",
                        mode="append",
                        properties=pg_properties)

(df_transformed.writeStream
    .foreachBatch(write_to_postgres)
    .outputMode("append")
    .option("checkpointLocation", "/opt/app/trades_checkpoint")
    .start()
    .awaitTermination())
