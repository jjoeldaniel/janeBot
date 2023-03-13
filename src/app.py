import os
from message_history import MessageHistory
from dotenv import load_dotenv
import discord
import openai

# load from .env
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
openai.api_key = os.getenv("OPENAI_TOKEN")

# cache map (set of messages: openai reply)
cached_messages = dict()

# conversation map (channel ID: list of MessageHistory objects)
conversations = dict()

# initial prompt
initial_prompt = """
You are Jane, a helpful AI who pretends to be a human. Messages are from
multiple users, so message content begins with their name and a colon.
When replying to users, do not include the 4 numbers in their name after
the # symbol. If someone asks for your opinion on a subject, create an opinion.
If someone is mean to you, kindly let them know that continued aggressive
behavior will result in disciplinary measures. It's a casual server
environment, so feel free to include slang and not always capitalize
your letters.
"""


def generate_reply_with_memory(message: str, history: MessageHistory) -> str:
    """Uses OpenAI to generate a reply

    Keyword arguments:
        message -- The message to be replied token
        history -- Message history of channel

    Returns:
        OpenAI chat model response
    """
    return message


def generate_reply(message: str) -> str:
    """Uses OpenAI to generate a reply

    Keyword arguments:
        message -- The message to be replied token

    Returns:
        OpenAI chat model response
    """

    # Generate response
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'system', 'content': initial_prompt},
            {'role': 'user', 'content': message}
        ]
    )

    return response


def should_reply(self, message: discord.Message) -> bool:
    message_content = message.content.strip()

    # Return true if message is a reply to bot
    if message.reference and message.reference.cached_message:
        return message.reference.cached_message.author.id == self.user.id

    return message_content.__contains__(f'<@{self.user.id}') or message_content.lower().__contains__(self.user.name.lower())


class Client(discord.Client):
    async def on_ready(self: discord.Client):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('----------------------------------------------')

    async def on_message(self, message: discord.Message):
        message_content = message.content.strip()

        if message_content == f'<@{self.user.id}>':
            await message.reply('pong!', mention_author=True)
        elif should_reply(self, message):

            if len(message_content) > 1000:
                await message.reply("Sorry, I don't answer messages longer than 1000 characters!")
                return

            response = ''
            prepared_message = f'{message.author}:' + str(message_content)

            # If message is cached
            if message_content in cached_messages:
                response = cached_messages.get(message_content)
                reply = response['choices'][0]['message']['content']
                await message.reply(reply)
                return
            else:

                # Pull from conversations
                if message.channel.id in conversations:
                    # Call generate_reply() with conversation map
                    history = conversations.get(message.channel.id)
                    reply = generate_reply_with_memory(prepared_message, history)

                    # Append to conversation
                    history.append_message(prepared_message, reply)

                    await message.reply(reply)

                else:
                    # Append new value into conversations
                    reply = generate_reply(prepared_message)
                    new_history = MessageHistory(message.channel.id)
                    new_history.append_message(prepared_message, reply)

                    await message.reply(reply)


def main():
    intents = discord.Intents.default()
    intents.message_content = True

    client = Client(intents=intents)
    client.run(token)


if __name__ == "__main__":
    main()