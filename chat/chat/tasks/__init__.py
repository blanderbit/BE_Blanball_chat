from chat.tasks.create_chat import (
    create_chat_consumer as create_chat_consumer
)
from chat.tasks.add_user_to_chat import (
    add_user_to_chat_consumer as add_user_to_chat_consumer
)


ALL_TASKS = [
    create_chat_consumer,
    add_user_to_chat_consumer,
]
