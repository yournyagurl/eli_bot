import discord
from discord.ext import commands
from db.dbcalls import DiscordBotCrud
import datetime
import logging
from discord.ui import Button, View
import asyncio

db_crud = DiscordBotCrud()

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} cog is online")

    @commands.command(name='inv')
    async def inventory(self, ctx):
        member = ctx.author
        member_id = member.id

        inventory = db_crud.get_inventory(member_id)

        if inventory:
            embed = discord.Embed(title="<a:pinktext:1326266668321607710> Inventory", color=discord.Color.from_rgb(249,177,181))
            for item_name, quantity in inventory:
                embed.add_field(name=item_name, value=f"Quantity: {quantity}", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("<:pinkexclamationmark:1326270444679991296> Your inventory is empty.")

    async def shop(self, ctx):
        shop_items = db_crud.get_shop_items()
        items_per_page = 10

        if not shop_items:
            await ctx.send("<:pinkexclamationmark:1326270444679991296> There are no items available in the shop.")
            return

        pages = []
        for i in range(0, len(shop_items), items_per_page):
            embed = discord.Embed(title="<a:pinktext:1326266668321607710> Shop Items", color=discord.Color.from_rgb(249,177,181))
            for item_name, item_price in shop_items[i:i + items_per_page]:
                embed.add_field(name=item_name, value=f"Price: {item_price}", inline=False)
            pages.append(embed)

        if len(pages) == 1:
            await ctx.send(embed=pages[0])
            return

        current_page = 0

        async def get_view(page_num):
            view = View()
            if page_num > 0:
                view.add_item(Button(label="Previous", style=discord.ButtonStyle.primary, custom_id="prev"))
            if page_num < len(pages) - 1:
                view.add_item(Button(label="Next", style=discord.ButtonStyle.primary, custom_id="next"))
            return view

        async def send_page(page_num):
            page_embed = pages[page_num]
            view = await get_view(page_num)
            message = await ctx.send(embed=page_embed, view=view)
            return message

        message = await send_page(current_page)

        while True:
            def check(interaction):
                return interaction.message.id == message.id and interaction.user == ctx.author

            try:
                interaction = await commands.wait_for("interaction", check=check, timeout=60.0)
            except asyncio.TimeoutError:
                break

            if interaction.data['custom_id'] == 'next':
                current_page += 1
                await interaction.response.edit_message(embed=pages[current_page], view=await get_view(current_page))
            elif interaction.data['custom_id'] == 'prev':
                current_page -= 1
                await interaction.response.edit_message(embed=pages[current_page], view=await get_view(current_page))



    @commands.command(name='additem')
    async def add_item(self, ctx):
        try:
            # Ask for the item details in one message
            await ctx.send("<:pinkexclamationmark:1326270444679991296> Please provide the details of the item in the following format:\n"
                        "`<item_name>, <price>, <consumable (yes/no)>, <role_assigned or 'none'>`")
            
            # Wait for the user's input
            item_details = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)

            # Split the message by commas
            details = item_details.content.split(',')

            # Ensure there are exactly 4 components
            if len(details) != 4:
                await ctx.send("<:pinkexclamationmark:1326270444679991296> Invalid format! Please provide exactly 4 details: `<item_name>, <price>, <consumable (yes/no)>, <role_assigned or 'none'>`")
                return

            # Step 2: Process and validate inputs
            item_name = details[0].strip()  # Item name
            try:
                item_price = int(details[1].strip())  # Convert price to integer
            except ValueError:
                await ctx.send("<:pinkexclamationmark:1326270444679991296> Invalid price! Please provide a valid number.")
                return
            
            # Convert consumable status to boolean
            consumable_status = details[2].strip().lower()
            if consumable_status not in ['yes', 'no']:
                await ctx.send("<:pinkexclamationmark:1326270444679991296> Invalid consumable status! Please type 'yes' or 'no'.")
                return
            is_consumable = consumable_status == 'yes'

            # Handle the role, treating 'none' as None
            role_assigned = details[3].strip().lower()
            role = None if role_assigned == 'none' else role_assigned

            # Step 3: Add the item to the database
            db_crud.add_shop_item(item_name, item_price, is_consumable, role)

            # Step 4: Confirmation message
            await ctx.send(f"Item '{item_name}' has been added to the shop.")

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")




    @commands.command(name='deleteitem')
    async def delete_item(self, ctx, item_name):
        try:
            # Attempt to delete the item from the shop
            item_deleted = db_crud.delete_shop_item(item_name)
            
            if item_deleted:
                await ctx.send(f"<:pinkexclamationmark:1326270444679991296> The item **{item_name}** has been deleted from the shop.")
            else:
                await ctx.send(f"<:pinkexclamationmark:1326270444679991296> No item named **{item_name}** found in the shop, or there was an error deleting it.")
        except Exception as e:
            await ctx.send(f"<:pinkexclamationmark:1326270444679991296> An error occurred while deleting the item: {e}")



    @commands.command(name="buy")
    async def buy_item(self, ctx, item_name: str):
        """Allow users to buy items from the shop."""
        member = ctx.author

        # Normalize the user-provided item name to lowercase for case-insensitive matching
        normalized_item_name = item_name.lower()

        # Fetch shop items and normalize their names to lowercase for comparison
        shop_items = db_crud.get_shop_items()
        item = next((item for item in shop_items if item[0].lower() == normalized_item_name), None)

        if not item:
            embed = discord.Embed(
                description="<:pinkexclamationmark:1326270444679991296> This item does not exist in the shop.",
                color=discord.Color.from_rgb(249,177,181)  # Pink color
            )
            await ctx.send(embed=embed)
            return

        item_price = item[1]  # Item price
        cash_balance = db_crud.get_cash(member.id)

        if cash_balance < item_price:
            embed = discord.Embed(
                description="<:pinkexclamationmark:1326270444679991296> You don't have enough cash to buy this item.",
                color=discord.Color.from_rgb(249,177,181)  # Pink color
            )
            await ctx.send(embed=embed)
            return

        db_crud.remove_cash(member.id, item_price)
        db_crud.add_inventory_item(member.id, item[0])  # Use the original case for adding to inventory

        embed = discord.Embed(
        title="Purchase Successful!",
        description=f"<a:pinktext:1326266668321607710> Congratulations! You have bought **{item_name}** for **{item_price}** cash.",
        color=discord.Color.from_rgb(249,177,181)  # Pink color
    )
        await ctx.send(embed=embed)


    


    @commands.command(name='giveItem')
    async def give_item(self, ctx, item_name: str = None, member: discord.Member = None):
        """Add an item to a member's inventory (for debugging purposes)."""
        if ctx.message.author.guild_permissions.administrator:
            if member is None:
                member = ctx.author

            if item_name is None:
                embed = discord.Embed(
                    title="Missing Item Name",
                    description="Please specify an item name to give.",
                    color=discord.Color.from_rgb(249,177,181)
                )
                await ctx.send(embed=embed)
                return

            try:
                # Ensure item_name is a string (not strictly necessary in this case)
                item_name_str = str(item_name)
            except ValueError:
                embed = discord.Embed(
                    title="Invalid Command Format",
                    description="Correct usage: **`;giveItem <item name> @<user>`**",
                    color=discord.Color.from_rgb(249,177,181)
                )
                await ctx.send(embed=embed)
                return

            # Log the addition and add the item to the database
            print(f"Adding {item_name} 🍀 to Member ID: {member.id}")
            db_crud.add_inventory_item(member.id, item_name_str)
            logging.info(f"Added {item_name} to Member ID: {member.id}")

            embed = discord.Embed(
                title="Item Added",
                description=f"Successfully added **{item_name}** 🍀 to **{member.display_name}**'s account.",
                color=discord.Color.from_rgb(249,177,181)
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Permission Denied",
                description="You do not have permission to use this command.",
                color=discord.Color.from_rgb(249,177,181)
            )
            await ctx.send(embed=embed)

    async def give_role(self, ctx, role_name_or_id: str, member: discord.Member):
        guild = ctx.guild
        try:
            # Attempt to retrieve the role by ID first
            role = discord.utils.get(guild.roles, id=int(role_name_or_id))
            if not role:
                # If role ID retrieval fails, attempt to retrieve by name
                role = discord.utils.get(guild.roles, name=role_name_or_id)

            if role:
                # Check if the user already has the role
                if role in member.roles:
                    await ctx.send(f"{member.mention} already has the **{role.name}** role.")
                else:
                    # Assign the role to the member
                    await member.add_roles(role)
                    await ctx.send(f"Assigned role **{role.name}** to {member.mention}.")
            else:
                await ctx.send(f"Role '{role_name_or_id}' not found.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(name='use')
    async def use_item(self, ctx, member: discord.Member, *, item_name: str):
        member_id = ctx.author.id  # Get the ID of the command invoker (ctx.author)
        guild = ctx.guild

        try:
            role_identifier = db_crud.use_inventory_item(member_id, item_name)

            if role_identifier:
                # Check if role_identifier is a name or ID
                try:
                    role_id = int(role_identifier)
                    role = discord.utils.get(guild.roles, id=role_id)
                except ValueError:
                    role = discord.utils.get(guild.roles, name=role_identifier)

                if role:
                    # Check if the bot has permission to manage roles for the member
                    if not ctx.guild.me.guild_permissions.manage_roles:
                        await ctx.send(f"<a:pinktext:1326266668321607710> {ctx.author.mention}, I do not have permission to manage roles.")
                        return

                    # Check if the bot's role is higher than the role to be assigned
                    if role.position >= ctx.guild.me.top_role.position:
                        await ctx.send(f"<a:pinktext:1326266668321607710> {ctx.author.mention}, I cannot assign the role '{role.name}' because it is higher than my highest role.")
                        return

                    # Assign the role using the give_role function
                    await self.give_role(ctx, str(role.id), member)
                    logging.info(f"<a:pinktext:1326266668321607710> {member} used {item_name} and received the {role.name} role.")
                else:
                    await ctx.send(f"{ctx.author.mention}, you have successfully used {item_name}, but the role '{role_identifier}' does not exist or I cannot assign it.")
                    logging.warning(f"<a:pinktext:1326266668321607710> Role '{role_identifier}' not found or cannot be assigned by {commands.user}.")
            else:
                await ctx.send(f"{ctx.author.mention}, you have successfully used {item_name}.")
                logging.info(f"<a:pinktext:1326266668321607710> {ctx.author} used {item_name} without receiving a role.")
        except ValueError as e:
            await ctx.send(f"<a:pinktext:1326266668321607710> {ctx.author.mention}, an error occurred: {e}")
            logging.error(f"ValueError occurred while using item '{item_name}': {e}")
        except discord.Forbidden:
            await ctx.send(f"<a:pinktext:1326266668321607710> {ctx.author.mention}, I do not have permission to manage roles.")
            logging.error(f"Bot does not have permission to manage roles.")
        except Exception as e:
            await ctx.send(f"<a:pinktext:1326266668321607710> {ctx.author.mention}, an unexpected error occurred: {e}")
            logging.exception(f"Unexpected error occurred while using item '{item_name}': {e}")

    @commands.command(name='shop')
    @commands.has_permissions(administrator=True)
    async def display_shop(self, ctx):
        shop_items = db_crud.get_shop_items()

        if not shop_items:
            await ctx.send("<a:pinktext:1326266668321607710> The shop is currently empty.")
            return

        # Create an embed to display shop items
        embed = discord.Embed(title="Shop Items", description="<a:pinktext:1326266668321607710> Here's a list of items available in the shop:", color=0x00ff00)

        for item_name, item_price in shop_items:
            embed.add_field(name=item_name, value=f"Price: {item_price} coins", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Shop(bot))


