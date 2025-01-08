import discord
from discord.ext import commands
import time
import sqlite3
from datetime import datetime

class VoiceTracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Set up a connection to your SQLite database (adjust the path as needed)
        self.conn = sqlite3.connect('discord_bot.db')  # Replace with your database path
        self.cursor = self.conn.cursor()

        # Create table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS UserActivity (
                MemberId INTEGER PRIMARY KEY,
                MessagesSent INTEGER,
                LastMessageTime DATETIME,
                MinutesInVC INTEGER,
                LastVCTimestamp DATETIME,
                XP INTEGER
            )
        ''')
        self.conn.commit()

        # A dictionary to store join times for users
        self.user_voice_times = {}

    # Helper function to update user's VC time and XP in the database
    def update_vc_time(self, member_id, time_spent):
        self.cursor.execute('''
            SELECT MinutesInVC, XP FROM UserActivity WHERE MemberId = ?
        ''', (member_id,))
        result = self.cursor.fetchone()

        xp_earned = int(time_spent * 2)  # XP is 2 per minute

        if result:
            # Update the MinutesInVC and XP if the user already exists
            new_time = result[0] + time_spent
            new_xp = result[1] + xp_earned
            self.cursor.execute('''
                UPDATE UserActivity SET MinutesInVC = ?, XP = ?, LastVCTimestamp = ? WHERE MemberId = ?
            ''', (new_time, new_xp, datetime.now(), member_id))
        else:
            # If the user doesn't exist in the database, insert a new entry
            self.cursor.execute('''
                INSERT INTO UserActivity (MemberId, MinutesInVC, LastVCTimestamp, XP) VALUES (?, ?, ?, ?)
            ''', (member_id, time_spent, datetime.now(), xp_earned))
        
        self.conn.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Check if the user has joined a voice channel
        if before.channel is None and after.channel is not None:
            # User joined a voice channel
            self.user_voice_times[member.id] = time.time()  # Store the current time when they join
        
        # Check if the user has left a voice channel
        elif before.channel is not None and after.channel is None:
            # User left a voice channel
            if member.id in self.user_voice_times:
                join_time = self.user_voice_times.pop(member.id)  # Get and remove the join time
                time_spent = (time.time() - join_time) / 60  # Time spent in VC in minutes
                print(f"{member.name} spent {time_spent:.2f} minutes in the voice channel.")
                
                # Update the database with the time spent and earned XP
                self.update_vc_time(member.id, time_spent)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} has connected to Discord.')

async def setup(bot):
   await bot.add_cog(VoiceTracking(bot))
