from typing import Any

from kafka import KafkaProducer
from django.conf import settings


def default_producer(topic_name: str, data: Any) -> None:
    producer: KafkaProducer = KafkaProducer(**settings.KAFKA_PRODUCER_CONFIG)
    producer.send(topic_name, value=data)
    producer.flush()
