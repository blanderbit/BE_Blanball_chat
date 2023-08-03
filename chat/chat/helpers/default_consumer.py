from importlib import import_module
from typing import Any

from django.conf import settings
from kafka import KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic

from chat.exceptions import (
    COMPARED_CHAT_EXCEPTIONS,
)
from chat.helpers.default_producer import (
    default_producer,
)
from chat.utils import (
    RESPONSE_STATUSES,
    add_request_data_to_response,
    generate_response,
)


def read_topics_from_file(filename: str) -> list[str]:
    with open(filename, "r") as file:
        topics = [topic.strip() for topic in file.readlines()]
    return topics


def create_topics() -> list:
    admin_client: KafkaAdminClient = KafkaAdminClient(**settings.KAFKA_ADMIN_CONFIG)
    all_kafka_topics = read_topics_from_file("../kafka_topics_list.txt")
    existing_topics = admin_client.list_topics()
    consumer_topics = [
        NewTopic(name=topic, num_partitions=1, replication_factor=1)
        for topic in all_kafka_topics
        if not (topic.endswith("response") or topic in existing_topics)
    ]
    admin_client.create_topics(new_topics=consumer_topics, validate_only=False)
    return admin_client.list_topics()


def default_consumer() -> None:
    consumer: KafkaConsumer = KafkaConsumer(**settings.KAFKA_CONSUMER_CONFIG)
    topics_to_subscribe = create_topics()

    consumer.subscribe(topics_to_subscribe)
    while True:
        raw_messages = consumer.poll(timeout_ms=100, max_records=200)
        for topic_partition, messages in raw_messages.items():
            for message in messages:
                topic_name: str = message.topic

                chat_task = import_module(f"chat.tasks.{topic_name}")

                try:
                    response_data: dict[str, Any] = {}
                    valid_data: dict[str, Any] = chat_task.validate_input_data(
                        message.value
                    )

                    topic_function = getattr(chat_task, topic_name)

                    if valid_data is not None:
                        response_data = topic_function(data=message.value, **valid_data)
                    else:
                        response_data = topic_function(data=message.value)
                    default_producer(
                        f"{topic_name}_response",
                        generate_response(
                            status=RESPONSE_STATUSES["SUCCESS"],
                            data=response_data,
                            message_type=topic_name,
                            request_data=add_request_data_to_response(message.value),
                        ),
                    )
                except COMPARED_CHAT_EXCEPTIONS as err:
                    print(err)
                    default_producer(
                        f"{topic_name}_response",
                        generate_response(
                            status=RESPONSE_STATUSES["ERROR"],
                            data=str(err),
                            message_type=topic_name,
                            request_data=add_request_data_to_response(message.value),
                        ),
                    )
