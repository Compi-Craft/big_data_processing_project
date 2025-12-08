FROM docker.io/spark:3.5.1

USER root

# Install cron and required packages
RUN apt-get update && apt-get install -y cron && \
    rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /opt/app

# Copy Spark job and cron setup
COPY precomputed_reports.py jobs/precomputed_reports.py
COPY spark-cron.sh spark-cron.sh
COPY crontab.txt /etc/cron.d/spark-job-cron

RUN pip3 install backports.zoneinfo pytz

# Set proper permissions and ensure newline at end of crontab
RUN chmod +x spark-cron.sh && \
    chmod 0644 /etc/cron.d/spark-job-cron && \
    echo "" >> /etc/cron.d/spark-job-cron && \
    touch /var/log/spark-job.log && \
    chmod 666 /var/log/spark-job.log

# Create entrypoint script to start cron properly
RUN echo '#!/bin/bash' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo 'echo "=== Starting cron daemon ==="' >> /entrypoint.sh && \
    echo '# Ensure log file exists and is writable' >> /entrypoint.sh && \
    echo 'touch /var/log/spark-job.log && chmod 666 /var/log/spark-job.log' >> /entrypoint.sh && \
    echo '# Verify crontab file exists and has correct format' >> /entrypoint.sh && \
    echo 'echo "Crontab file content:"' >> /entrypoint.sh && \
    echo 'cat /etc/cron.d/spark-job-cron' >> /entrypoint.sh && \
    echo '# Test script execution' >> /entrypoint.sh && \
    echo 'echo "Testing cron script execution..."' >> /entrypoint.sh && \
    echo '/opt/app/spark-cron.sh >> /var/log/spark-job.log 2>&1 || echo "Initial test failed"' >> /entrypoint.sh && \
    echo 'echo "Test execution completed. Check /var/log/spark-job.log for details"' >> /entrypoint.sh && \
    echo '# Install crontab using crontab command' >> /entrypoint.sh && \
    echo 'crontab /etc/cron.d/spark-job-cron' >> /entrypoint.sh && \
    echo 'echo "Crontab installed via crontab command:"' >> /entrypoint.sh && \
    echo 'crontab -l' >> /entrypoint.sh && \
    echo '# Start cron in foreground mode' >> /entrypoint.sh && \
    echo 'echo "Starting cron in foreground mode..."' >> /entrypoint.sh && \
    echo 'exec cron -f' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
