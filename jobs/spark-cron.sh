#!/bin/bash

LOG_FILE="/var/log/spark-job.log"

echo "[$(date)] spark-cron.sh started as $(whoami)" >> "$LOG_FILE"

# Find Java home (standard Spark image uses OpenJDK)
if [ -z "$JAVA_HOME" ]; then
  # Try standard Spark image location first
  if [ -d /opt/java/openjdk ]; then
    export JAVA_HOME=/opt/java/openjdk
  elif [ -f /usr/bin/java ]; then
    JAVA_PATH=$(readlink -f /usr/bin/java 2>/dev/null || echo "/usr/bin/java")
    export JAVA_HOME=$(dirname "$(dirname "$JAVA_PATH")")
  elif [ -f /opt/java/openjdk/bin/java ]; then
    export JAVA_HOME=/opt/java/openjdk
  elif [ -d /usr/lib/jvm ]; then
    JAVA_HOME=$(find /usr/lib/jvm -name "java" -type f 2>/dev/null | head -1 | xargs dirname | xargs dirname 2>/dev/null)
    if [ -n "$JAVA_HOME" ]; then
      export JAVA_HOME
    fi
  fi
fi

if [ -n "$JAVA_HOME" ] && [ -d "$JAVA_HOME" ]; then
  export PATH=$JAVA_HOME/bin:$PATH
  echo "[$(date)] JAVA_HOME set to: $JAVA_HOME" >> "$LOG_FILE"
else
  # Try to get JAVA_HOME from java command
  if command -v java &> /dev/null; then
    JAVA_HOME_CMD=$(java -XshowSettings:properties -version 2>&1 | grep "java.home" | awk '{print $3}')
    if [ -n "$JAVA_HOME_CMD" ]; then
      export JAVA_HOME="$JAVA_HOME_CMD"
      export PATH=$JAVA_HOME/bin:$PATH
      echo "[$(date)] JAVA_HOME set from java command to: $JAVA_HOME" >> "$LOG_FILE"
    else
      echo "[$(date)] WARNING: JAVA_HOME not set, using system default" >> "$LOG_FILE"
    fi
  else
    echo "[$(date)] ERROR: Java not found in system" >> "$LOG_FILE"
    exit 1
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
  echo "[$(date)] ERROR: spark-submit not found" >> "$LOG_FILE"
  exit 1
fi

echo "[$(date)] Using spark-submit: $SPARK_SUBMIT" >> "$LOG_FILE"

# Check if jars directory exists and collect jar files
JARS_DIR="/opt/spark-jars"
JAR_FILES=""
if [ -d "$JARS_DIR" ]; then
  JAR_FILES=$(find "$JARS_DIR" -name "*.jar" 2>/dev/null | tr '\n' ',' | sed 's/,$//')
  if [ -n "$JAR_FILES" ]; then
    echo "[$(date)] Found JAR files: $JAR_FILES" >> "$LOG_FILE"
  else
    echo "[$(date)] WARNING: No JAR files found in $JARS_DIR" >> "$LOG_FILE"
  fi
else
  echo "[$(date)] WARNING: JAR directory $JARS_DIR does not exist" >> "$LOG_FILE"
fi

# Check if Python script exists
PYTHON_SCRIPT="/opt/app/jobs/precomputed_reports.py"
if [ ! -f "$PYTHON_SCRIPT" ]; then
  echo "[$(date)] ERROR: Python script not found: $PYTHON_SCRIPT" >> "$LOG_FILE"
  exit 1
fi

# Build spark-submit command
SPARK_CMD="$SPARK_SUBMIT"
SPARK_CMD="$SPARK_CMD --conf spark.jars.ivy=/opt/app"

if [ -n "$JAR_FILES" ]; then
  SPARK_CMD="$SPARK_CMD --jars $JAR_FILES"
fi

SPARK_CMD="$SPARK_CMD --master spark://spark-master:7077"
SPARK_CMD="$SPARK_CMD --deploy-mode client"
SPARK_CMD="$SPARK_CMD --conf spark.executor.memory=512m"
SPARK_CMD="$SPARK_CMD --conf spark.cores.max=1"
SPARK_CMD="$SPARK_CMD $PYTHON_SCRIPT"

echo "[$(date)] Executing: $SPARK_CMD" >> "$LOG_FILE"

# Execute spark-submit
eval "$SPARK_CMD" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "[$(date)] spark-submit completed successfully" >> "$LOG_FILE"
else
  echo "[$(date)] ERROR: spark-submit failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

exit $EXIT_CODE
