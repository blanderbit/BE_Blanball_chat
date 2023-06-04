from kafka import KafkaConsumer
from django.conf import settings

def base_consumer():
    consumer = KafkaConsumer('my_topic', **settings.KAFKA_CONSUMER_CONFIG)
    for message in consumer:
        print("Consumer 1:", message.value)