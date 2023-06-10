from typing import Any

from django.conf import settings
from kafka import KafkaProducer


def default_producer(topic_name: str, data: Any) -> None:
    producer: KafkaProducer = KafkaProducer(**settings.KAFKA_PRODUCER_CONFIG)
    producer.send(topic_name, value=data)
    producer.flush()
