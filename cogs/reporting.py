import discord
from discord.ext import commands

class Report(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.report_channel_id = 1326297421722161265  # Replace with your report channel's ID

    @commands.command(name="report")
    async def report(self, ctx, *, reason: str = "No reason provided"):
        """
        Report a replied-to message to the moderators.
        """
        # Check if the user replied to a message
        if not ctx.message.reference:
            await ctx.send("Please reply to the message you want to report, and provide a reason.")
            return

        try:
            # Get the referenced message
            replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            # Get the report channel
            report_channel = ctx.guild.get_channel(self.report_channel_id)
            if not report_channel:
                await ctx.send("Report channel is not set up. Please contact an admin.")
                return

            # Build the report embed
            embed = discord.Embed(title="Message Report", color=discord.Color.from_rgb(249,177,181))
            embed.add_field(name="Reported By", value=ctx.author.mention, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(
                name="Reported Message",
                value=f"[Jump to Message]({replied_message.jump_url})\n**Content:** {replied_message.content}",
                inline=False,
            )
            embed.add_field(name="Author of Reported Message", value=replied_message.author.mention, inline=False)
            embed.set_footer(text=f"Reported in #{replied_message.channel.name}")
            embed.timestamp = discord.utils.utcnow()

            # Send the report to the moderation channel
            await report_channel.send(embed=embed)

            # Confirm the report to the user
            await ctx.send("Thank you for your report. The moderation team has been notified.")

        except discord.Forbidden:
            await ctx.send("I do not have permission to send messages to the report channel. Please contact an admin.")
        except discord.HTTPException as e:
            await ctx.send(f"An unexpected error occurred: {e}")

# Required setup function for the cog
async def setup(bot):
    await bot.add_cog(Report(bot))
