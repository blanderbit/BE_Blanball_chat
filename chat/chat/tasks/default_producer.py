from typing import Any

from kafka import KafkaProducer
from django.conf import settings


def default_producer(data: Any, topic_name: str) -> None:
    producer: KafkaProducer = KafkaProducer(**settings.KAFKA_PRODUCER_CONFIG)
    producer.send(topic_name, value=data)
    producer.flush()
