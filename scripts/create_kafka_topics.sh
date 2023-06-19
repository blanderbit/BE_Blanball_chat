#!/bin/bash
kafka_container_name="blanball-chat-kafka"
kafka_exec_command="docker exec $kafka_container_name kafka-topics"

topics_file="../kafka_topics_list.txt"
topics=$(cat "$topics_file")

# Создание топиков
for topic in $topics; do
  $kafka_exec_command --create \
    --bootstrap-server localhost:9092 \
    --topic "$topic" \
    --partitions 1 \
    --replication-factor 1
done