FROM docker.io/spark:3.5.1

USER root

# Install cron
RUN apt-get update && apt-get install -y cron

# Create working directory
WORKDIR /opt/app

# Copy Spark job and cron setup
COPY precomputed_reports.py jobs/precomputed_reports.py
COPY spark-cron.sh spark-cron.sh
COPY crontab.txt /etc/cron.d/spark-job-cron

RUN pip3 install backports.zoneinfo pytz



RUN chmod +x spark-cron.sh && \
    chmod 0644 /etc/cron.d/spark-job-cron && \
    crontab /etc/cron.d/spark-job-cron && \
    touch /var/log/spark-job.log

CMD ["cron", "-f"]
