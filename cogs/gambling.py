import discord
import random
import asyncio
from discord.ext import commands
from db.dbcalls import DiscordBotCrud
import logging
import traceback

db_crud = DiscordBotCrud()

class SlotsGame:
    def __init__(self):
        self.symbols = ['🍒', '🍋', '🔔', '🍉', '⭐', '7️⃣']

    def spin(self, win_chance=0.35):
        if random.random() < win_chance:
            # Create a winning combination
            symbol = random.choice(self.symbols)
            return [symbol, symbol, symbol]
        else:
            # Create a losing combination
            return random.choices(self.symbols, k=3)

    def calculate_winnings(self, bet_amount, result):
        if result[0] == result[1] == result[2]:
            return bet_amount * 2  # Jackpot
        else:
            return 0  # No win

    async def play_slots(self, ctx, bet_amount: int):
        member_id = ctx.author.id
        current_cash = db_crud.get_cash(member_id)  # Replace with your method to retrieve user's cash

        if bet_amount <= 0 or bet_amount > current_cash:
            embed = discord.Embed(title="Error!", description='Invalid bet amount.', color=discord.Color.from_rgb(249,177,181))
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
            return

        db_crud.remove_cash(member_id, bet_amount)

        result = self.spin()
        winnings = self.calculate_winnings(bet_amount, result)

        result_prompt = f"**Result:** {' '.join(result)}\n\n"

        if winnings > 0:
            self.add_cash(member_id, winnings)
            result_prompt += f"🎉  **Winner:**  🎉\n{ctx.author.mention} won {str(winnings)}!"
            color = discord.Color.green()
        else:
            result_prompt += "**No Winner :(**"
            color=discord.Color.from_rgb(249,177,181)

        embed = discord.Embed(title="Slots Result", description=result_prompt, color=color)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

        log_channel = ctx.guild.get_channel(1310756010662822009)
        if log_channel:
            log_embed = discord.Embed(
                title="Slots Game Log",
                description="Here's the outcome of a Slots game:",
                color=color
            )
            log_embed.add_field(name="User", value=ctx.author.display_name, inline=False)
            log_embed.add_field(name="Bet Amount", value=f"{bet_amount}", inline=False)
            log_embed.add_field(name="Result", value=f"{' '.join(result)}", inline=False)
            if winnings > 0:
                log_embed.add_field(name="**Win**", value=f"{winnings}", inline=False)
            else:
                log_embed.add_field(name="**Loss**", value=f"-{bet_amount}", inline=False)

            await log_channel.send(embed=log_embed)


class RouletteGame:
    def __init__(self):
        self.slots = {
            '0': 'green', '00': 'green', '1': 'red', '2': 'black', '3': 'red', '4': 'black', '5': 'red',
            '6': 'black', '7': 'red', '8': 'black', '9': 'red', '10': 'black', '11': 'black', '12': 'red', 
            '13': 'black', '14': 'red', '15': 'black', '16': 'red', '17': 'black', '18': 'red', '19': 'red', 
            '20': 'black', '21': 'red', '22': 'black', '23': 'red', '24': 'black', '25': 'red', '26': 'black', 
            '27': 'red', '28': 'black', '29': 'black', '30': 'red', '31': 'black', '32': 'red', '33': 'black', 
            '34': 'red', '35': 'black', '36': 'red'
        }

    async def play_roulette(self, ctx, bet_amount: int, space: str):
        member_id = ctx.author.id
        current_cash = db_crud.get_cash(member_id)  # Replace with your method to retrieve user's cash

        if bet_amount < 100 or bet_amount > current_cash or bet_amount > 1000:
            embed = discord.Embed(title="Error!", description='Invalid bet amount. Bet must be between 100 and 1000 and within your current cash.', color=discord.Color.from_rgb(249,177,181))
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
            await ctx.send(embed=embed)
            return

        db_crud.remove_cash(member_id, bet_amount)

        # Determine the multiplier based on the space bet on
        if space in ["odd", "even", "black", "red"]:
            multiplier = 2
        else:
            multiplier = 35

        result = random.choice(list(self.slots.keys()))
        result_prompt = f"The ball landed on: **{self.slots[result]} {result}**!\n\n"

        if space == "black":
            win = 1 if self.slots[result] == "black" else 0

        elif space == "red":
            win = 1 if self.slots[result] == "red" else 0

        elif space == "even":
            result_num = int(result)
            win = 1 if (result_num % 2) == 0 else 0

        elif space == "odd":
            result_num = int(result)
            win = 1 if (result_num % 2) != 0 else 0

        elif space.isdigit():  # Check if the space is a specific number
            win = 1 if space == result else 0

        else:
            # This should not happen under normal circumstances
            print("Unexpected condition.")

        if win:
            winnings = bet_amount * multiplier
            db_crud.add_cash(member_id, winnings)
            result_prompt += f"🎉  **Winner:**  🎉\n{ctx.author.mention} won {str(winnings)}!"
            color = discord.Color.green()
        else:
            result_prompt += "**No Winner :(**"
            color = discord.Color.from_rgb(249,177,181)

        embed = discord.Embed(title="Roulette Result", description=result_prompt, color=color)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

        log_channel = ctx.guild.get_channel(1310756010662822009)
        if log_channel:
            log_message = f"Roulette Result:\nUser: {ctx.author.display_name} ({ctx.author.id})\n"
            log_message += f"Bet Amount: {bet_amount}\nBet Space: {space}\n"
            log_message += f"Result: {self.slots[result]} {result}\n"
            if win:
                log_message += f"**Win:** {winnings}\n"
            else:
                log_message += f"**Loss:** -{bet_amount}\n"

            await log_channel.send(log_message)

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.roulette_game = RouletteGame()
        self.slots_game = SlotsGame()

        # Define the suits and values
        self.suits = ['♢', '♧', '♡', '♤']
        self.values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

        # Create a full deck of cards (note the use of self to refer to values)
        self.deck = [f'{value}{suit}' for suit in self.suits for value in self.values]

    # Other methods and functions will go here...
    # Card values for blackjack
    card_values = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 10, 'Q': 10, 'K': 10, 'A': 11
    }

    def deal_card(self):
        return random.choice(self.deck)

    # Calculate hand value
    def calculate_hand_value(self, hand):
        value = sum(self.card_values[card[:-1]] for card in hand)
        aces = sum(1 for card in hand if card[:-1] == 'A')
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    error_color = discord.Color.from_rgb(204, 0, 0)

    @commands.command(name='blackjack')
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def blackjack(self, ctx, bet: int):
        member_id = ctx.author.id
        current_cash = db_crud.get_cash(member_id)

        if bet < 100 or bet > 1000:
            embed = discord.Embed(title="<:pinkexclamationmark:1326270444679991296> Error!", description='Bet must be between 100 and 1000.', color=discord.Color.from_rgb(249,177,181))
            await ctx.send(embed=embed)
            self.blackjack.reset_cooldown(ctx)
            return

        if current_cash < bet:
            embed = discord.Embed(title="<:pinkexclamationmark:1326270444679991296> Error!", description=f'You do not have enough cash to place this bet. Your current cash is {current_cash}.', color=discord.Color.from_rgb(249,177,181))
            await ctx.send(embed=embed)
            self.blackjack.reset_cooldown(ctx)
            return

        # Deduct the bet from the player's cash
        db_crud.remove_cash(member_id, bet)

        player_hand = [self.deal_card(), self.deal_card()]
        dealer_hand = [self.deal_card(), self.deal_card()]

        embed = discord.Embed(title="Blackjack", description=f"Bet: {bet}", color=discord.Color.from_rgb(249,177,181))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        embed.add_field(name="Your Hand", value=f'{" ".join(player_hand)} (value: {self.calculate_hand_value(player_hand)})', inline=False)
        embed.add_field(name="Dealer's Hand", value=f'{dealer_hand[0]} ?', inline=False)

        message = await ctx.send(embed=embed)

        while self.calculate_hand_value(player_hand) < 21:
            await ctx.send('Do you want to hit or stand? (respond with `hit` or `stand`)')

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['hit', 'stand']

            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send('You took too long to respond. Standing by default.')
                break

            if msg.content.lower() == 'hit':
                player_hand.append(self.deal_card())
                embed.set_field_at(0, name="Your Hand", value=f'{" ".join(player_hand)} (value: {self.calculate_hand_value(player_hand)})', inline=False)
                await message.edit(embed=embed)
            else:
                break

        player_value = self.calculate_hand_value(player_hand)
        if player_value > 21:
            await ctx.send(f'You busted with a hand value of {player_value}. You lose your bet of {bet}.')
            return

        embed.set_field_at(1, name="Dealer's Hand", value=f'{" ".join(dealer_hand)} (value: {self.calculate_hand_value(dealer_hand)})', inline=False)
        await message.edit(embed=embed)

        while self.calculate_hand_value(dealer_hand) < 17:
            dealer_hand.append(self.deal_card())
            embed.set_field_at(1, name="Dealer's Hand", value=f'{" ".join(dealer_hand)} (value: {self.calculate_hand_value(dealer_hand)})', inline=False)
            await message.edit(embed=embed)

        dealer_value = self.calculate_hand_value(dealer_hand)
        if dealer_value > 21:
            await ctx.send(f'Dealer busts with a hand value of {dealer_value}. You win {bet * 2}!')
            db_crud.add_cash(member_id, bet * 2)
        elif dealer_value > player_value:
            await ctx.send(f'Dealer wins with {dealer_value} against your {player_value}. You lose your bet of {bet}.')
        elif dealer_value < player_value:
            await ctx.send(f'You win with {player_value} against dealer\'s {dealer_value}. You win {bet * 2}!')
            db_crud.add_cash(member_id, bet * 2)
        else:
            await ctx.send(f'It\'s a tie with both having {player_value}. Your bet of {bet} is returned.')
            db_crud.add_cash(member_id, bet)

    @commands.Cog.listener()
    async def blackjack_error(self, ctx, error):

        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Nuh uh!", 
                description=f"You're going too fast. Try again in {int(error.retry_after // 3600)} hours.", 
                color=discord.Color.from_rgb(249,177,181)
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error!", 
                description='Please enter a valid bet amount between 100 and 1000.', 
                color=discord.Color.from_rgb(249,177,181)
            )
            await ctx.send(embed=embed)
            await ctx.send(f"To retry the command, use: `;blackjack <bet_amount>` (e.g., `;blackjack 500`)")
            # Reset cooldown for this specific user in this specific context
            await self.blackjack.reset_cooldown(ctx)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Error!", 
                description='Please enter a valid numerical bet amount.', 
                color=discord.Color.from_rgb(249,177,181)
            )
            await ctx.send(embed=embed)
            await ctx.send(f"To retry the command, use: `;blackjack <bet_amount>` (e.g., `;blackjack 500`)")
            # Reset cooldown for this specific user in this specific context
            await self.blackjack.reset_cooldown(ctx)
        else:
            # Default error handling
            embed = discord.Embed(
                title="Error!", 
                description="Something went wrong.", 
                color=discord.Color.from_rgb(249,177,181)
            )
            await ctx.send(embed=embed)
            await ctx.send(f"To retry the command, use: `;blackjack <bet_amount>` (e.g., `;blackjack 500`)")

    @commands.command(name='roulette')
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def roulette(self, ctx, bet_amount: int, space: str):
        if space not in ["odd", "even", "black", "red"] and not space.isdigit():
            embed = discord.Embed(title="Error!", description="Invalid space. Please bet on 'odd', 'even', 'black', 'red', or a specific number (0-36).", color=discord.Color.from_rgb(249,177,181))
            await ctx.send(embed=embed)
            return
        await self.roulette_game.play_roulette(ctx, bet_amount, space)

    @roulette.error
    async def roulette_error(self, ctx, error):
        traceback.print_exc()
        
        # Reset the cooldown for this specific user in this specific context
        await self.roulette.reset_cooldown(ctx)
        
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(title="Nuh uh!", description=f"You're going too fast. Try again in {int(error.retry_after // 3600)} hours.", color=discord.Color.from_rgb(249,177,181))
            await ctx.send(embed=embed)
        
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(title="Error!", description='Please enter a valid bet amount between 100 and 1000, and a color (red or black).', color=discord.Color.from_rgb(249,177,181))
            await ctx.send(embed=embed)
            await ctx.send(f"To retry the command, use: `;roulette <bet_amount> <color>` (e.g., `;roulette 400 red`)")
        
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="Error!", description='Please enter a valid numerical bet amount and a valid color (red or black).', color=discord.Color.from_rgb(249,177,181))
            await ctx.send(embed=embed)
            await ctx.send(f"To retry the command, use: `;roulette <bet_amount> <color>` (e.g., `;roulette 400 red`)")

        else:
            # Default error handling
            embed = discord.Embed(title="Error!", description="Something went wrong.", color=discord.Color.from_rgb(249,177,181))
            await ctx.send(embed=embed)
            await ctx.send(f"To retry the command, use: `;roulette <bet_amount> <color>` (e.g., `;roulette 400 red`)")

    @commands.command(name='slots')
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def slots(ctx, bet_amount: int):
        await SlotsGame.play_slots(ctx, bet_amount)

    @slots.error
    async def slots_error(ctx, error):
        traceback.print_exc()
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Nuh uh!",
                description=f"You're going too fast. Try again in {error.retry_after // 3600} hours.",
                color=discord.Color.from_rgb(249,177,181)
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error!",
                description='Please enter a valid bet amount between 100 and 1000.',
                color=discord.Color.from_rgb(249,177,181)
            )
            await ctx.send(embed=embed)
            ctx.command.reset_cooldown(ctx)  # Reset cooldown for the command
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Error!",
                description='Please enter a valid numerical bet amount.',
                color=discord.Color.from_rgb(249,177,181)
            )
            await ctx.send(embed=embed)
        else:
            # Default error handling
            embed = discord.Embed(
                title="Error!",
                description="Something went wrong.",
                color=discord.Color.from_rgb(249,177,181)
            )
            await ctx.send(embed=embed)


    




# Required setup function for the cog
async def setup(bot):
    await bot.add_cog(Gambling(bot))
