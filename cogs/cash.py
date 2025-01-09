import discord
from discord.ext import commands
from db.dbcalls import DiscordBotCrud
import datetime
import logging

db_crud = DiscordBotCrud()

class Cash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # Update with your actual database file path
        self.logger = logging.getLogger(__name__)

    @commands.command(name='addCash')
    async def addcash(self, ctx, member: discord.Member = None, cash: int = None):
        """Add Cash to member"""
        
        # Allow bot owner to bypass permission checks
        if not await self.bot.is_owner(ctx.author):
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("You don't have permissions to use this command.")
                return

        if member is None:
            await ctx.send("Please mention a valid member.")
            return
        
        if cash is None:
            await ctx.send("Please provide a valid amount of Money to add.")
            return
        
        try:
            cash_int = int(cash)
        except ValueError:
            await ctx.send("Invalid amount. Please provide a valid integer.")
            return

        print(f"Adding {cash_int} Cash to Member ID: {member.id}")
        db_crud.add_cash(member.id, cash_int)
        logging.info(f"Added {cash_int} Cash to Member ID: {member.id}")
        await ctx.send(f"Added {cash_int} Cash to {member.mention}.")

    @addcash.error
    async def addcash_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permissions to use this command.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid arguments provided. Usage: `;addCash @member amount`.")
        else:
            await ctx.send("An unexpected error occurred. Please try again later.")

    @commands.command(name='removeCash')
    async def removecash(self, ctx, member: discord.Member = None, cash: int = None):
        """Add Cash to member"""
    #  if not ctx.message.author.guild_permissions.administrator:
    #     await ctx.send("You don't have permission to use this command.")
        #    return
        
        if member is None:
            await ctx.send("Please mention a valid member.")
            return
        
        if cash is None:
            await ctx.send("Please provide a valid amount of XP to add.")
            return
        
        try:
            cash_int = int(cash)
        except ValueError:
            await ctx.send("Invalid amount. Please provide a valid integer.")
            return

        print(f"Removing {cash_int} Cash to Member ID: {member.id}")
        db_crud.remove_cash(member.id, cash_int)
        logging.info(f"Removed {cash_int} Cash to Member ID: {member.id}")
        await ctx.send(f"Removed {cash_int} Cash to {member.display_name}.")

    @commands.command(name="lb-cash")
    async def lb_cash(self, ctx):
        """Fetches and displays the top 9 XP leaderboard."""
        self.logger.debug("Command +xp_cash invoked.")

        # Get the top users based on XP from the database
        try:
            top_users_xp = db_crud.get_top_cash()  # Ensure db_crud.get_top_xp() is defined properly
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
            title="Top 10 Cash Leaderboard",
            description=description,
            color=discord.Color.from_rgb(249,177,181)  # You can choose any color you prefer
        )

        # Send the embed with the leaderboard to the channel
        await ctx.send(embed=embed)

    
    




    

async def setup(bot):
    await bot.add_cog(Cash(bot))
