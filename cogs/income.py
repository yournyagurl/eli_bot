import discord
from discord.ext import commands
from db.dbcalls import DiscordBotCrud  # Assuming this is your database class
from datetime import timedelta, datetime
import logging

db_crud = DiscordBotCrud()  # Initialize your database CRUD class

class Income(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} cog is online")

    # Define roles and associated income and cooldowns
    daily_role_names = ["Verified 18+"]  # Replace with your roles
    daily_income_amount = 500
    weekly_role_income = {
        "Efflorescent": 5000,  
        "₊˚໒ Staff ୭₊˚": 2500,
        "Vanity Link": 2000,
        "Bronze Clover": 2000,
    }

    @commands.command(name="collect")
    async def collect(self, ctx):
        """Combine daily and weekly income into a single command."""
        member = ctx.author
        now = datetime.utcnow()

        # Initialize response messages and total income
        daily_message, weekly_message = "", ""
        total_income = 0

        # Check for daily income eligibility
        if any(role.name in self.daily_role_names for role in member.roles):
            last_daily_claim = db_crud.get_lastclaimtime(member.id, 'daily')
            if last_daily_claim:
                last_daily_claim = datetime.fromisoformat(last_daily_claim)  # Convert if it's a string
                if (now - last_daily_claim).days >= 1:
                    # Eligible for daily income
                    db_crud.add_cash(member.id, self.daily_income_amount)
                    db_crud.update_lastclaimtime(member.id, 'daily', now.isoformat())
                    total_income += self.daily_income_amount
                    daily_message = f"<a:pinktext:1326266668321607710> **Daily Income**: <:pinkclover:1326218907341688915>  {self.daily_income_amount}."
                else:
                    # Show time left until next claim
                    next_claim_time = last_daily_claim + timedelta(days=1)
                    time_left = next_claim_time - now
                    hours, minutes = divmod(int(time_left.total_seconds() / 60), 60)
                    daily_message = f"<:pinkexclamationmark:1326270444679991296> **Daily income** : **{hours}hr {minutes}min**"
            else:
                # First claim, grant daily income
                db_crud.add_cash(member.id, self.daily_income_amount)
                db_crud.update_lastclaimtime(member.id, 'daily', now.isoformat())
                total_income += self.daily_income_amount
                daily_message = f"<a:pinktext:1326266668321607710> **Daily Income**: <:pinkclover:1326218907341688915>  {self.daily_income_amount}."

        else:
            daily_message = "<a:pinktext:1326266668321607710> Verify or boost to get income!"

        # Check for weekly income eligibility
        member_roles = [role.name for role in member.roles if role.name in self.weekly_role_income]
        if member_roles:
            last_weekly_claim = db_crud.get_lastclaimtime(member.id, 'weekly')
            if last_weekly_claim:
                last_weekly_claim = datetime.fromisoformat(last_weekly_claim)  # Convert if it's a string
                if (now - last_weekly_claim).days >= 7:
                    # Eligible for weekly income
                    weekly_income = sum(self.weekly_role_income[role] for role in member_roles)
                    db_crud.add_cash(member.id, weekly_income)
                    db_crud.update_lastclaimtime(member.id, 'weekly', now.isoformat())
                    total_income += weekly_income
                    weekly_message = f"<a:pinktext:1326266668321607710> **Weekly Income**: <:pinkclover:1326218907341688915> {weekly_income}."
                else:
                    # Show time left until next claim
                    next_claim_time = last_weekly_claim + timedelta(weeks=1)
                    time_left = next_claim_time - now
                    days, hours = divmod(int(time_left.total_seconds() / 3600), 24)
                    weekly_message = f"<:pinkexclamationmark:1326270444679991296> **Weekly Income** : **{days}d {hours}hr**"
            else:
                # First claim, grant weekly income
                weekly_income = sum(self.weekly_role_income[role] for role in member_roles)
                db_crud.add_cash(member.id, weekly_income)
                db_crud.update_lastclaimtime(member.id, 'weekly', now.isoformat())
                total_income += weekly_income
                weekly_message = f"<a:pinktext:1326266668321607710> **Weekly Income**: <:pinkclover:1326218907341688915> {weekly_income}."

        else:
            weekly_message = "<:pinkexclamationmark:1326270444679991296> Verify or boost to get income!."

        # Build the body of the message by combining both daily and weekly messages
        income_message = f"{daily_message}\n\n{weekly_message}"

        # Build and send income status embed
        embed = discord.Embed(title="Income Status", description=income_message, color=discord.Color.from_rgb(249,177,181))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Income(bot))
