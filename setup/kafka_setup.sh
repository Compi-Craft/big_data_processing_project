#!/bin/bash

for t in trades orders; do
  kafka-topics.sh --create \
    --if-not-exists \
    --bootstrap-server kafka:9092 \
    --replication-factor 1 \
    --partitions 1 \
    --topic "$t"
done