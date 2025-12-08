#!/bin/bash

echo "[$(date)] spark-cron.sh started as $(whoami)" >> /var/log/spark-job.log

# Find Java home (standard Spark image uses OpenJDK)
if [ -z "$JAVA_HOME" ]; then
  if [ -f /usr/bin/java ]; then
    export JAVA_HOME=$(readlink -f /usr/bin/java | sed "s:bin/java::")
  elif [ -d /usr/lib/jvm ]; then
    export JAVA_HOME=$(find /usr/lib/jvm -name "java" -type f | head -1 | xargs dirname | xargs dirname)
  fi
fi

# Use system Python (standard Spark image includes Python)
export PYSPARK_PYTHON=python3
export PYSPARK_DRIVER_PYTHON=python3

# Use spark-submit from PATH or standard locations
if command -v spark-submit &> /dev/null; then
  SPARK_SUBMIT=spark-submit
elif [ -f /opt/spark/bin/spark-submit ]; then
  SPARK_SUBMIT=/opt/spark/bin/spark-submit
elif [ -f /usr/local/spark/bin/spark-submit ]; then
  SPARK_SUBMIT=/usr/local/spark/bin/spark-submit
else
  echo "ERROR: spark-submit not found" >> /var/log/spark-job.log
  exit 1
fi

$SPARK_SUBMIT \
  --conf spark.jars.ivy=/opt/app \
  --jars /opt/spark-jars/*.jar \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --conf spark.executor.memory=512m \
  --conf spark.cores.max=1 \
  /opt/app/jobs/precomputed_reports.py
