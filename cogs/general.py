import discord
from discord.ext import commands
from db.dbcalls import DiscordBotCrud
import datetime
import logging

db_crud = DiscordBotCrud()


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} cog is online")

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"Pong! Latency: {round(self.bot.latency * 1000)}ms.")

    @commands.command(name="stats")
    async def stats(self, ctx, member: discord.Member = None):
        """Show stats for the user who invoked the command or another specified member."""
        # If no member is mentioned, use the invoking user
        if member is None:
            member = ctx.author

        # Ensure the member exists in the server
        if member is None:
            await ctx.send("That member is not in the server.")
            return

        # Fetch the user's data from the database
        try:
            user_activity = db_crud.get_user_activity(member.id)  # Using the member's ID
            if user_activity:
                messages_sent = user_activity['MessagesSent']
                xp = user_activity['XP']
                minutes_in_vc = user_activity.get('MinutesInVC', 0)  # Default to 0 if no VC time is recorded
                cash = user_activity.get('Cash', 0)  # Default to 0 if no Cash is recorded

                # Create the embed for displaying the stats
                embed = discord.Embed(
                    title=f"Stats for {member.name}",
                    color=discord.Color.from_rgb(249,177,181),
                    description=(
                        f"<:BabyPinkArrowRight:1326221748676591717>**Messages Sent:** {messages_sent} messages\n"
                        f"<:BabyPinkArrowRight:1326221748676591717>**XP:** {xp} XP\n"
                        f"<:BabyPinkArrowRight:1326221748676591717>**Minutes in VC:** {minutes_in_vc:.2f} minutes\n"
                        f"<:BabyPinkArrowRight:1326221748676591717>**Cash:** <:pinkclover:1326218907341688915>{cash}"
                    )
                )

                # Send the embed with the stats
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Could not find stats for {member.name}. Please make sure they've been active.")
        except Exception as e:
            print(f"Error fetching user stats for {member.name}: {e}")
            await ctx.send("An error occurred while fetching the stats. Please try again later.")



    @commands.command(name="lb-xp")
    async def xp_leaderboard(self, ctx):
        """Fetches and displays the top 9 XP leaderboard."""
        self.logger.debug("Command +xp_leaderboard invoked.")

        # Get the top users based on XP from the database
        try:
            top_users_xp = db_crud.get_top_xp()  # Ensure db_crud.get_top_xp() is defined properly
            self.logger.debug(f"Fetched top users: {top_users_xp}")
        except Exception as e:
            self.logger.error(f"Error fetching top users: {e}")
            await ctx.send("Error fetching leaderboard data.")
            return

        # If no data is found, send a message indicating so
        if not top_users_xp:
            self.logger.warning("No leaderboard data found.")
            await ctx.send("No leaderboard data available.")
            return

        # Define the rank emotes for the leaderboard
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

        # Prepare the leaderboard message
        description = ""
        for rank, (member_id, xp) in enumerate(top_users_xp, start=1):
            try:
                # Fetch member using the MemberId
                member = await ctx.bot.fetch_user(member_id)  # Correct way to fetch a user
                member_name = member.name if member else f"User Left ({member_id})"
            except discord.NotFound:
                self.logger.warning(f"Member {member_id} not found. Assuming user left.")
                member_name = f"User Left ({member_id})"
            except Exception as e:
                self.logger.error(f"Error fetching member {member_id}: {e}")
                member_name = f"Unknown User ({member_id})"

            # Get the appropriate emote for the rank
            emote = rank_emotes.get(rank, f"Rank {rank}")  # Default to just the rank number if not in emotes

            # Add the emote and user data to the description
            description += f"{emote} {member_name} - {xp} XP\n"

        # Create the embed for a more formatted leaderboard display
        embed = discord.Embed(
            title="Top 10 XP Leaderboard",
            description=description,
            color=discord.Color.from_rgb(249,177,181)  # You can choose any color you prefer
        )

        # Send the embed with the leaderboard to the channel
        await ctx.send(embed=embed)

    @commands.command(name='addXp')
    async def addxp(self, ctx, member: discord.Member = None, xp: int = None):
        """Add xp to member"""
    #  if not ctx.message.author.guild_permissions.administrator:
    #     await ctx.send("You don't have permission to use this command.")
        #    return
        
        if member is None:
            await ctx.send("Please mention a valid member.")
            return
        
        if xp is None:
            await ctx.send("Please provide a valid amount of XP to add.")
            return
        
        try:
            xp_int = int(xp)
        except ValueError:
            await ctx.send("Invalid amount. Please provide a valid integer.")
            return

        print(f"Adding {xp_int} XP to Member ID: {member.id}")
        db_crud.add_xp(member.id, xp_int)
        logging.info(f"Added {xp_int} XP to Member ID: {member.id}")
        await ctx.send(f"Added {xp_int} XP to {member.display_name}.")

    @commands.command(name='removeXp')
    async def removexp(self, ctx, member: discord.Member = None, xp: int = None):
        """Remove xp to member"""
    #  if not ctx.message.author.guild_permissions.administrator:
    #     await ctx.send("You don't have permission to use this command.")
        #    return
        
        if member is None:
            await ctx.send("Please mention a valid member.")
            return
        
        if xp is None:
            await ctx.send("Please provide a valid amount of XP to add.")
            return
        
        try:
            xp_int = int(xp)
        except ValueError:
            await ctx.send("Invalid amount. Please provide a valid integer.")
            return

        print(f"Removed {xp_int} XP to Member ID: {member.id}")
        db_crud.remove_xp(member.id, xp_int)
        logging.info(f"Removed {xp_int} XP to Member ID: {member.id}")
        await ctx.send(f"Removed {xp_int} XP to {member.display_name}.")



# Required setup function for the cog
async def setup(bot):
    await bot.add_cog(General(bot))
