import discord
from discord.ext import commands, tasks
from db.dbcalls import DiscordBotCrud
import datetime
import json
import os

CONFIG_FILE = "config.json"

# Save and load the leaderboard configuration
def save_leaderboard_config(channel_id, chatlb_message_id, voicelb_message_id):
    try:
        with open("leaderboard_config.json", "w") as f:
            json.dump({
                "channel_id": channel_id,
                "chat_message_id": chatlb_message_id,
                "voice_message_id": voicelb_message_id
            }, f)
            print("Leaderboard config saved successfully.")
    except Exception as e:
        print(f"Error saving leaderboard config: {e}")



def load_leaderboard_config():
    try:
        with open("leaderboard_config.json", "r") as f:
            config = json.load(f)
        return config.get("channel_id"), config.get("chat_message_id"), config.get("voice_message_id")
    except FileNotFoundError:
        return None, None

db_crud = DiscordBotCrud()

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.leaderboard_channel_id, self.leaderboard_message_id, self.voicelb_message_id = load_leaderboard_config()
        self.update_leaderboard.start()  # Start the task to update the leaderboard

    def cog_unload(self):
        self.update_leaderboard.cancel()  # Stop the task when the cog is unloaded

    @commands.command(name="set_leaderboard_channel")
    @commands.has_permissions(administrator=True)
    async def set_leaderboard_channel(self, ctx):
        """Set the leaderboard channel and post the first leaderboard message."""
        # Check if a leaderboard channel is already set
        if self.leaderboard_channel_id:
            await ctx.send("Leaderboard channel is already set. Use `reset_leaderboard` to reconfigure.")
            return
        
        # Log the action to debug
        print(f"Setting leaderboard channel to {ctx.channel.id}")

        # Set the current channel as the leaderboard channel
        self.leaderboard_channel_id = ctx.channel.id  

        # Create the initial leaderboard embeds
        chat_embed = await self.generate_chat_leaderboard_embed()
        voice_embed = await self.generate_voice_leaderboard_embed()

        # Send the first leaderboard messages
        try:
            chat_message = await ctx.channel.send(embed=chat_embed)
            voice_message = await ctx.channel.send(embed=voice_embed)

            # Save the message IDs for updates
            self.leaderboard_message_id = chat_message.id
            self.voicelb_message_id = voice_message.id

            # Save to the configuration file
            save_leaderboard_config(self.leaderboard_channel_id, self.leaderboard_message_id, self.voicelb_message_id)

            await ctx.send(f"Leaderboard channel set to {ctx.channel.mention} and messages initialized.")
        except Exception as e:
            print(f"Error while sending leaderboard messages: {e}")
            await ctx.send("An error occurred while setting the leaderboard. Please try again.")

    @commands.command(name="reset_leaderboard")
    @commands.has_permissions(administrator=True)
    async def reset_leaderboard(self, ctx):
        """Reset the leaderboard configuration."""
        self.leaderboard_channel_id = None
        self.leaderboard_message_id = None
        self.voicelb_message_id = None
        save_leaderboard_config(None, None, None)
        await ctx.send("Leaderboard configuration has been reset. You can now set a new leaderboard channel.")

    @tasks.loop(hours=4)
    async def update_leaderboard(self):
        """Update the leaderboard messages every 4 hours."""
        
        # Update Chat Leaderboard
        if self.leaderboard_channel_id and self.leaderboard_message_id:
            channel = self.bot.get_channel(self.leaderboard_channel_id)
            if not channel:
                print("Leaderboard channel not found.")
            else:
                try:
                    # Fetch the chat leaderboard message
                    message = await channel.fetch_message(self.leaderboard_message_id)
                    if not message:
                        print("Chat leaderboard message not found.")
                    else:
                        # Update the chat leaderboard message
                        embed = await self.generate_chat_leaderboard_embed()
                        await message.edit(embed=embed)
                except discord.NotFound:
                    print("Chat leaderboard message not found.")
                except discord.Forbidden:
                    print("Missing permissions to fetch or edit the message.")
                except discord.HTTPException as e:
                    print(f"Failed to update chat leaderboard: {e}")
        
        # Update Voice Leaderboard
        if self.leaderboard_channel_id and self.voicelb_message_id:
            channel = self.bot.get_channel(self.leaderboard_channel_id)
            if not channel:
                print("Leaderboard channel not found.")
            else:
                try:
                    # Fetch the voice leaderboard message
                    message = await channel.fetch_message(self.voicelb_message_id)
                    if not message:
                        print("Voice leaderboard message not found.")
                    else:
                        # Update the voice leaderboard message
                        embed = await self.generate_voice_leaderboard_embed()
                        await message.edit(embed=embed)
                except discord.NotFound:
                    print("Voice leaderboard message not found.")
                except discord.Forbidden:
                    print("Missing permissions to fetch or edit the message.")
                except discord.HTTPException as e:
                    print(f"Failed to update voice leaderboard: {e}")

    async def generate_chat_leaderboard_embed(self):
        """Generate the chat leaderboard embed."""
        top_users = db_crud.get_top_chat_users()  # Get top chat users from DB

        if not top_users:
            return discord.Embed(
                title="Chat Leaderboard",
                description="No data available for the chat leaderboard.",
                color=discord.Color.from_rgb(249,177,181)
            )

        # Rank emotes
        rank_emotes = {
            1: "<a:6322number1:1320173918018994227>",
            2: "<a:1656number2:1320173926952861828>",
            3: "<a:5370number3:1320173933789450340>",
            4: "<a:9120number4:1320173924688068640>",
            5: "<a:3422number5:1320173930522083339>",
            6: "<a:8334number6:1320173921018052718>",
            7: "<a:3009number7:1320173928458485983>",
            8: "<a:8617number8:1320173922448179260>",
            9: "<a:4029number9:1320173932325896273>",
        }

        # Limit to top 9
        top_users = top_users[:9]

        # Build the leaderboard description
        description = ""
        for i, (member_id, messages_sent) in enumerate(top_users, start=1):
            emote = rank_emotes.get(i, "")
            member = self.bot.get_user(member_id)
            member_name = member.name if member else f"User Left ({member_id})"
            description += f"{emote} **{member_name}** - {messages_sent} messages\n"

        # Create the embed
        embed = discord.Embed(
            title="CHAT LEADERBOARD (LAST 7 DAYS)",
            description=description,
            color=discord.Color.from_rgb(249,177,181)
        )
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"Last updated: {current_time}")
        return embed

    async def generate_voice_leaderboard_embed(self):
        """Generate the voice leaderboard embed."""
        top_users = db_crud.get_top_voice_users()  # Get top voice users from DB

        if not top_users:
            return discord.Embed(
                title="Voice Leaderboard",
                description="No data available for the voice leaderboard.",
                color=discord.Color.from_rgb(249,177,181)
            )

        # Rank emotes for voice (you can reuse or customize the same rank emotes)
        rank_emotes = {
            1: "<a:6322number1:1320173918018994227>",
            2: "<a:1656number2:1320173926952861828>",
            3: "<a:5370number3:1320173933789450340>",
            4: "<a:9120number4:1320173924688068640>",
            5: "<a:3422number5:1320173930522083339>",
            6: "<a:8334number6:1320173921018052718>",
            7: "<a:3009number7:1320173928458485983>",
            8: "<a:8617number8:1320173922448179260>",
            9: "<a:4029number9:1320173932325896273>",
        }

        # Limit to top 9
        top_users = top_users[:9]

        # Build the leaderboard description
        description = ""
        for i, (member_id, minutes_spent) in enumerate(top_users, start=1):
            emote = rank_emotes.get(i, "")
            member = self.bot.get_user(member_id)
            member_name = member.name if member else f"User Left ({member_id})"
            description += f"{emote} **{member_name}** - {minutes_spent:.2f} minutes\n"

        # Create the embed
        embed = discord.Embed(
            title="VOICE LEADERBOARD (LAST 7 DAYS)",
            description=description,
            color=discord.Color.from_rgb(249,177,181)
        )
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"Last updated: {current_time}")
        return embed
    
    

# Required setup function for the cog
async def setup(bot):
    await bot.add_cog(Leaderboard(bot))