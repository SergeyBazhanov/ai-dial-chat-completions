import asyncio

from task.clients.client import DialClient
from task.constants import DEFAULT_SYSTEM_PROMPT
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role


async def start(stream: bool) -> None:
    client = DialClient(deployment_name="gpt-4")

    conversation = Conversation()

    system_prompt_input = input(
        "Enter system prompt (or press Enter for default): "
    ).strip()
    system_prompt = (
        system_prompt_input if system_prompt_input else DEFAULT_SYSTEM_PROMPT
    )

    system_message = Message(role=Role.SYSTEM, content=system_prompt)
    conversation.add_message(system_message)

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if not user_input:
            continue

        user_message = Message(role=Role.USER, content=user_input)
        conversation.add_message(user_message)

        print("Assistant: ", end="", flush=True)

        if stream:
            assistant_message = await client.stream_completion(
                conversation.get_messages()
            )
        else:
            assistant_message = client.get_completion(conversation.get_messages())

        conversation.add_message(assistant_message)


try:
    asyncio.run(start(True))
except KeyboardInterrupt:
    pass
