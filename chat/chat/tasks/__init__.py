from chat.tasks.create_chat import (
    create_chat_consumer as create_chat_consumer
)
from chat.tasks.add_user_to_chat import (
    add_user_to_chat_consumer as add_user_to_chat_consumer
)
from chat.tasks.remove_user_from_chat import (
    remove_user_from_chat_consumer as remove_user_from_chat_consumer
)
from chat.tasks.delete_chat import (
    delete_chat_consumer as delete_chat_consumer
)


ALL_TASKS = [
    create_chat_consumer,
    add_user_to_chat_consumer,
    remove_user_from_chat_consumer,
    delete_chat_consumer,
]
