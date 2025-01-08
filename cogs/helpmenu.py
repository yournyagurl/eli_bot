import discord
from discord.ext import commands
import asyncio
import logging

class Helpmenu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} cog is online")

    async def paginate(self, ctx, embeds):
        current_page = 0

        message = await ctx.send(embed=embeds[current_page])

        # Add navigation buttons
        await message.add_reaction('⬅️')
        await message.add_reaction('➡️')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️'] and reaction.message.id == message.id

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

                if str(reaction.emoji) == '➡️' and current_page < len(embeds) - 1:
                    current_page += 1
                    await message.edit(embed=embeds[current_page])
                elif str(reaction.emoji) == '⬅️' and current_page > 0:
                    current_page -= 1
                    await message.edit(embed=embeds[current_page])

                await message.remove_reaction(reaction.emoji, user)

            except asyncio.TimeoutError:
                # Clear reactions after timeout
                await message.clear_reactions()
                break

    @commands.command(name="info")
    async def info(self, ctx):
        embeds = []

        embed1 = discord.Embed(title="Basic Commands", color=discord.Color.from_rgb(249, 177, 181))
        embed1.add_field(name="Ping", value="Print bot latency", inline=False)
        embed1.add_field(name="+stats", value="Displays your current stats", inline=False)
        embeds.append(embed1)

        embed2 = discord.Embed(title="XP Commands", color=discord.Color.from_rgb(249, 177, 181))
        embed2.add_field(name="+addXp (number) @(member)", value="Add XP to a member", inline=False)
        embed2.add_field(name="+removeXp (number) @(member)", value="Remove XP from a member", inline=False)
        embed2.add_field(name="+ResetXp (@everyone/ @role/ @member)", value="Reset user XP to 0", inline=False)
        embed2.add_field(name="+lb-xp", value="Show XP leaderboard", inline=False)
        embeds.append(embed2)

        embed3 = discord.Embed(title="Cash Commands", color=discord.Color.from_rgb(249, 177, 181))
        embed3.add_field(name="+addCash (number) @(member)", value="Add Cash to a member", inline=False)
        embed3.add_field(name="+removeCash (number) @(member)", value="Remove Cash from a member", inline=False)
        embed3.add_field(name="+collect", value="Collect income", inline=False)
        embed3.add_field(name="+lb-cash", value="Show Cash leaderboard", inline=False)
        embeds.append(embed3)

        embed4 = discord.Embed(title="Gambling and Shop", color=discord.Color.from_rgb(249, 177, 181))
        embed4.add_field(name="+inv", value="Display member inventory", inline=False)
        embed4.add_field(name="+buy (item name)", value="Buy a shop item", inline=False)
        embed4.add_field(name="+use @(member) (item name)", value="Use an item", inline=False)
        embed4.add_field(name="+blackjack (amount)", value="Start a game of blackjack", inline=False)
        embed4.add_field(name="+roulette (amount) (color/value)", value="Start a game of roulette", inline=False)
        embeds.append(embed4)

        await self.paginate(ctx, embeds)

# Required setup function for the cog
async def setup(bot):
    await bot.add_cog(Helpmenu(bot))
