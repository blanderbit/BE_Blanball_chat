from chat.tasks.add_user_to_chat import (
    add_user_to_chat_consumer as add_user_to_chat_consumer,
)
from chat.tasks.create_chat import (
    create_chat_consumer as create_chat_consumer,
)
from chat.tasks.create_message import (
    create_message_consumer as create_message_consumer,
)
from chat.tasks.delete_chat import (
    delete_chat_consumer as delete_chat_consumer,
)
from chat.tasks.delete_messages import (
    delete_messages_consumer,
)
from chat.tasks.disable_chat import (
    disable_chat_consumer as disable_chat_consumer,
)
from chat.tasks.edit_chat import (
    edit_chat_consumer as edit_chat_consumer,
)
from chat.tasks.edit_message import (
    edit_message_consumer as edit_message_consumer,
)
from chat.tasks.get_chat_messages_list import (
    get_chat_messages_list_consumer as get_chat_messages_list_consumer,
)
from chat.tasks.get_chat_users_list import (
    get_chat_users_list_consumer as get_chat_users_list_consumer,
)
from chat.tasks.get_chats_list import (
    get_chats_list_consumer as get_chats_list_consumer,
)
from chat.tasks.read_or_unread_messages import (
    read_or_unread_messages_consumer,
)
from chat.tasks.remove_user_from_chat import (
    remove_user_from_chat_consumer as remove_user_from_chat_consumer,
)
from chat.chat.tasks.set_or_unset_chat_admin import (
    set_or_unset_chat_admin_consumer as set_or_unset_chat_admin_consumer
)

ALL_TASKS = [
    create_chat_consumer,
    add_user_to_chat_consumer,
    remove_user_from_chat_consumer,
    delete_chat_consumer,
    disable_chat_consumer,
    edit_chat_consumer,
    get_chats_list_consumer,
    create_message_consumer,
    edit_message_consumer,
    get_chat_messages_list_consumer,
    read_or_unread_messages_consumer,
    delete_messages_consumer,
    get_chat_users_list_consumer,
    set_or_unset_chat_admin_consumer,
]
