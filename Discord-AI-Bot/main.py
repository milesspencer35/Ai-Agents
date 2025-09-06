import discord
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

# Initialize the clients
discord_client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(discord_client)
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Keep track of which threads the bot should respond in
active_threads = set()

# Keep conversation history per thread
thread_histories = {}  # key: thread.id, value: list of messages
MAX_HISTORY_LENGTH = 10


@discord_client.event
async def on_ready():
    await tree.sync()  # syncs slash commands with Discord
    print(f"We have logged in as {discord_client.user}")


# Helper: split a long message into chunks <= 2000 characters
def chunk_message(text, max_length=2000):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


@tree.command(name="chat", description="Start a private thread and ask the bot a question")
@discord.app_commands.describe(question="What do you want to ask?")
async def chat_command(interaction: discord.Interaction, question: str):
    # Create a private thread
    thread = await interaction.channel.create_thread(
        name=f"{interaction.user.display_name}'s Chat",
        type=discord.ChannelType.private_thread
    )

    # Add only the user who invoked the command
    await thread.add_user(interaction.user)

    active_threads.add(thread.id)

    # Initialize conversation history for this thread
    thread_histories[thread.id] = [{"role": "user", "content": question}]

    # Ephemeral confirmation to the user
    await interaction.response.send_message(
        "Created a private thread! I’ll respond there.",
        ephemeral=True
    )

    # Post the question + AI response in the thread
    await thread.send(f"**You asked:** {question}")

    async with thread.typing():
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=300,
            messages=thread_histories[thread.id]
        )
        reply = response.choices[0].message.content

    # Append the bot's reply to history and trim if necessary
    thread_histories[thread.id].append({"role": "assistant", "content": reply})
    if len(thread_histories[thread.id]) > MAX_HISTORY_LENGTH:
        thread_histories[thread.id] = thread_histories[thread.id][-MAX_HISTORY_LENGTH:]

    for chunk in chunk_message(reply, 2000):
        await thread.send(chunk)


@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    channel = message.channel
    if channel.id in active_threads:
        # Append user's message to history
        thread_histories[channel.id].append({"role": "user", "content": message.content})
        if len(thread_histories[channel.id]) > MAX_HISTORY_LENGTH:
            thread_histories[channel.id] = thread_histories[channel.id][-MAX_HISTORY_LENGTH:]

        async with channel.typing():
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=300,
                messages=thread_histories[channel.id]
            )
            reply = response.choices[0].message.content

        # Append bot reply to history and trim
        thread_histories[channel.id].append({"role": "assistant", "content": reply})
        if len(thread_histories[channel.id]) > MAX_HISTORY_LENGTH:
            thread_histories[channel.id] = thread_histories[channel.id][-MAX_HISTORY_LENGTH:]

        # Send in chunks
        for chunk in chunk_message(reply, 2000):
            await channel.send(chunk)


token = os.getenv('TOKEN')
if token is None:
    print("Error: TOKEN environment variable is not set!")
    print("Please set your Discord bot token in the environment variables.")
    exit(1)

discord_client.run(token)
