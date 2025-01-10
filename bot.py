import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import asyncio
from discord import Embed, Color
from db.dbcalls import DiscordBotCrud
from datetime import datetime

# Intents
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.voice_states = True
intents.message_content = True
intents.members = True

# Bot setup
bot = commands.Bot(command_prefix="+", intents=intents)
db_crud = DiscordBotCrud()
# Load environment variables

load_dotenv()
TOKEN = os.getenv('TOKEN')
CONSOLE = int(os.getenv('CONSOLE'))
if TOKEN is None:
    print("ERROR: Bot token not found. Check your .env file.")
    exit(1)

# Events
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Connected to {len(bot.guilds)} guild(s).")
    print("Bot is ready!")
    print(db_crud.get_user_activity(1201187317860290662))

    
    console_msg = bot.get_channel(CONSOLE)
    total_members = sum(guild.member_count for guild in bot.guilds)
    if console_msg:
        await console_msg.send(
            embed=discord.Embed(
                title="Bot running",
                description=f"Current member count : {total_members}",
                color=discord.Color.green()
            )
        )
    

    

@bot.event
async def on_member_join(member):
    """Handle when a member joins the server."""
    # Add member to the database
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_crud.add_member(member.id)
    print(f"Member added to database: {member.name} (ID: {member.id})")

    # Send message to console channel
    console_channel = bot.get_channel(CONSOLE)
    if console_channel:
        embed = discord.Embed(
            title="New Member Joined",
            description=f"Welcome {member.name} (ID: {member.id}) to the server!",
            color=discord.Color.red(),
        )
        embed.set_footer(text=f"Joined at {current_time}")
        await console_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    """Handle when a member leaves the server."""
    # Remove member from the database
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db_crud.remove_member(member.id)
    print(f"Member removed from database: {member.name} (ID: {member.id})")

    # Send message to console channel
    console_channel = bot.get_channel(CONSOLE)
    if console_channel:
        embed = discord.Embed(
            title="Member Left",
            description=f"{member.name} (ID: {member.id}) has left the server.",
            color=discord.Color.from_rgb(238, 159, 142),
        )
        embed.set_footer(text=f"Left at {current_time}")
        await console_channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    # Get the MemberId from the message author
    member_id = message.author.id

    # Call the function to update the message count
    db_crud.increment_messages_sent(member_id)

    # Process commands or other bot-related logic
    await bot.process_commands(message)

user_voice_times = {}


# Load cogs
async def Load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cog: {filename}")
            except Exception as e:
                print(f"Failed to load cog {filename}: {e}")

# Main function
async def main():
    async with bot:
        await Load()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
