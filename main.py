from discord.ext import commands, pages
from discord.utils import get
from colorama import Fore
from time import ctime
import discord
import json
import datetime
import pyperclip
import chat_exporter
import io
import uuid
from mongodb import save_view, delete_view, get_views, get_views_by_type, fetch_view_from_db, delete_view_from_db



# discord.Bot() is for application commands
# commands.Bot() is for prefix commands
# bridge.Bot() is for both application and prefix commands
intents = discord.Intents.default()
intents.guilds = True  # Enable the 'guilds' intent to access roles
intents.members = True
intents.presences = True
intents.message_content = True
bot = discord.Bot(intents=intents)

# Cool variable for styling etc
t = f"{Fore.LIGHTYELLOW_EX}{ctime()}{Fore.RESET}" 

# --------------------LOAD THE CONFIG--------------------

# probably best if you use a .env but I prefer to use json

with open('config.json', 'r') as file:
    config = json.load(file)

# Accessing individual values from the config
bot_token = config["BOT_TOKEN"]
bot_invite = config["BOT_INVITE"]
moderator_role_id = config["Moderator_Role_ID"]
allowed_roles = [1280532531313246229, 1280532531313246228, 1280532531313246230]
# --------------------------------------------------------

# runs when the bot is deployed/logged in
@bot.event
async def on_ready():
    print(f"{t}{Fore.LIGHTBLUE_EX} | Ready and online - {bot.user.display_name}\n{Fore.RESET}")
    keep_guild_ids = [979461945138745385, 1280532531258851338] #first wasp second project wl

    try:
        guild_count = 0
        for guild in bot.guilds:
            if guild.id in keep_guild_ids:
                print(f"{Fore.RED}- {guild.id} (name: {guild.name}) [KEEPING]\n{Fore.RESET}")
                guild_count += 1
                # print(f"{Fore.YELLOW}Roles in {guild.name} (ID: {guild.id}):")
                # for role in guild.roles:
                #     print(f" - Role Name: {role.name}, Role ID: {role.id}")
                # print(Fore.RESET)
            else:
                print(f"{Fore.RED}- {guild.id} (name: {guild.name}) [LEAVING]\n{Fore.RESET}")
                await guild.leave()  # Leave the guild
        
       
        print(f"{t}{Fore.LIGHTBLUE_EX} | {bot.user.display_name} is in {guild_count} guilds.\n{Fore.RESET}")

        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"/help")) 
        await load_persistent_views()
        await load_ticket_persistent_views()
        bot.add_view(TicketView())

    except Exception as e:
        print(e)


async def load_ticket_persistent_views():
    try:
        # Load all saved views
        all_views = get_views()  # Assuming this fetches all views, including ticket views, with view_id

        for view_data in all_views:
            view_id = view_data.get("view_id")
            if view_id:  # Only proceed if view_id is present
                ticket_view = TicketButtonView(
                    item_name=view_data.get("item_name"),
                    price_input=view_data.get("price"),
                    payment=view_data.get("payment"),
                    type=view_data.get("type"),
                    specific=view_data.get("specific"),
                    quantity=view_data.get("quantity"),
                    collateral=view_data.get("collateral"),
                    message_link= view_data.get("message_link"),
                    view_id=view_id
                )

                # Add the view directly without message binding
                bot.add_view(ticket_view)  
                print(f"Added persistent TicketButtonView with ID: {view_id}")

    except Exception as e:
        print(f"Failed to load persistent views: {e}")



async def load_persistent_views():

    try:
        # Load all saved sell views
        sell_views = get_views_by_type("sell")

        for view_data in sell_views:
            # Create a SellButtonView instance from the stored data
            sell_view = SellButtonView.from_dict(view_data)

            # Fetch the original message in Discord to re-bind the view
            if sell_view.message_link:
                try:
                    guild_id, channel_id, message_id = sell_view.message_link.split('/')[-3:]
                    channel = bot.get_channel(int(channel_id))

                    if channel:
                        message = await channel.fetch_message(int(message_id))
                        bot.add_view(sell_view, message_id=int(message_id))
                        print(f"Added persistent Sell view for message: {message.jump_url}")
                    else:
                        print(f"Channel not found for message link: {sell_view.message_link}")
                except Exception as e:
                    print(f"Error re-adding Sell view: {e}")

        # Load all saved buy views
        buy_views = get_views_by_type("buy")

        for view_data in buy_views:
            # Create a BuyButtonView instance from the stored data
            buy_view = BuyButtonView.from_dict(view_data)

            # Fetch the original message in Discord to re-bind the view
            if buy_view.message_link:
                try:
                    guild_id, channel_id, message_id = buy_view.message_link.split('/')[-3:]
                    channel = bot.get_channel(int(channel_id))

                    if channel:
                        message = await channel.fetch_message(int(message_id))
                        bot.add_view(buy_view, message_id=int(message_id))
                        print(f"Added persistent Buy view for message: {message.jump_url}")
                    else:
                        print(f"Channel not found for message link: {buy_view.message_link}")
                except Exception as e:
                    print(f"Error re-adding Buy view: {e}")

    except Exception as e:
        print(f"Failed to load persistent views: {e}")



@bot.event
async def on_message(message):
    
    target_channel_ids = {1286040525371347044, 1286040297876361250,1300149511754088548, 1303856291285827634}  
    if (
        message.channel.id in target_channel_ids
        and not message.content.startswith('/')
        and message.author != bot.user
    ):
        await message.delete()


# @bot.slash_command(name="clear_channels", description="Delete all previous messages in specified channels")
# @commands.has_permissions(administrator=True)  # Limit usage to admins for safety
# async def clear_channels(ctx: discord.ApplicationContext):
#     target_channel_ids = [1286040525371347044, 1286040297876361250,1300149511754088548, 1303856291285827634]  

#     for channel_id in target_channel_ids:
#         channel = bot.get_channel(channel_id)
#         if channel:
#             # Delete all messages in the channel
#             await channel.purge(limit=None)
#             await ctx.respond(f"Cleared messages in {channel.mention}", ephemeral=True)

#     await ctx.respond("All specified channels have been cleared.", ephemeral=True)



@bot.slash_command(name="help", description="Lists all commands")
@commands.cooldown(1, 3, commands.BucketType.user) # 3 second cooldown 
async def help_command(ctx: discord.ApplicationContext):

    
    command_info = [(command.name, command.description) for command in bot.commands]
    chunks = [command_info[i:i + 15] for i in range(0, len(command_info), 15)]
    pages_list = [
        discord.Embed(
            title="List of commands:",
            description="\n".join([f"`/{name}` - {description}" for name, description in chunk]),
            color=discord.Color.blurple()
        ) for chunk in chunks
    ]
    paginator = pages.Paginator(pages=pages_list, loop_pages=True, timeout=30)
    await paginator.respond(ctx.interaction, ephemeral=False)


async def ticket_button_callback(ctx):
    await ctx.respond(f"Thanks for clicking", ephemeral=True)


class MakeOfferSellModal(discord.ui.Modal):
    def __init__(self, item_name, chain, pricetype, price, payment, type, specific, quantity, collateral, project_link, message_link):
        super().__init__(title="Make an Offer")
        self.item_name = item_name
        self.chain = chain
        self.pricetype = pricetype
        self.price = price
        self.payment = payment
        self.type = type
        self.specific = specific
        self.quantity = quantity
        self.collateral = collateral
        self.project_link = project_link
        self.message_link = message_link

        self.price_input = discord.ui.InputText(
            label="Enter Valid Price", placeholder="Enter the price you wish to offer", style=discord.InputTextStyle.short
        )
        self.add_item(self.price_input)

        self.instructions_input = discord.ui.InputText(
            label="Specific Instructions", placeholder="Any specific instructions?", style=discord.InputTextStyle.long
        )
        self.add_item(self.instructions_input)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user

        creationEmbed = discord.Embed(
            title="Ticket Created",
            description= (
                f"{user.mention} your ticket has been created! Our team will be with you as soon as possible.\n"
                f"**Reason**\n"
                f"Want to buy [Click here]({self.message_link})"
            ),
            color=discord.Color.green()
        )
        creationEmbed.set_footer(text="Ticket System")
        creationEmbed.timestamp = datetime.datetime.now()

        # Create the embed message
        embed = discord.Embed(
            description=(
                f"**Item:** {self.item_name}\n\n"
                f"**Price for {self.pricetype}:** {self.price} => {self.price_input.value}\n\n"
                f"**Payment:** {self.payment}\n\n"
                f"**Type:** {self.type}\n\n"
                f"**Specific:** {self.specific} => {self.instructions_input.value}\n\n"
                f"**Quantity:** {self.quantity}\n\n"
                f"**Collateral:** {self.collateral}\n\n"
                f"**Project Link:** {self.project_link}\n\n"

            ),
            color=discord.Color.yellow()
        )
        embed.set_footer(text="Building trust in web3")
        embed.timestamp = datetime.datetime.now()

        await interaction.response.defer(ephemeral=True)
        category = discord.utils.get(interaction.guild.categories, name="Support Tickets")
        if category is None:
            await interaction.followup.send("The 'Tickets' category does not exist.", ephemeral=True)
            return
        
        channel_name = f"{user.name}-{self.item_name}".lower()
        mod_role = get(interaction.guild.roles, name="Middlemen")

        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites={
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
                mod_role: discord.PermissionOverwrite(read_messages=True, send_messages=True) if mod_role else None
            }
        )
        await channel.edit(topic=f"Refer to the original message here: {self.message_link}")

        

        mentions = [user.mention]
        mentions.append(f" <@&{moderator_role_id}>")
        mention_message = " ".join(mentions)
        await channel.send(mention_message)
        await channel.send(embed=creationEmbed, view=TicketButtonView(self.message_link, self.item_name, self.price_input, self.payment,self.type, self.specific,self.quantity, self.collateral ))
        await channel.send(embed=embed)
        await interaction.followup.send(f"Your ticket has been created: {channel.mention}", ephemeral=True)

class MakeOfferBuyModal(discord.ui.Modal):
    def __init__(self, item_name, chain, pricetype, price, payment, type, specific, quantity, collateral, project_link, message_link, view_id):
        super().__init__(title="Make an Offer")
        self.item_name = item_name
        self.chain = chain
        self.pricetype = pricetype
        self.price = price
        self.payment = payment
        self.type = type
        self.specific = specific
        self.quantity = quantity
        self.collateral = collateral
        self.project_link = project_link
        self.message_link = message_link
        self.view_id = view_id

        self.price_input = discord.ui.InputText(
            label="Enter Valid Price", placeholder="Enter the price you wish to offer", style=discord.InputTextStyle.short
        )
        self.add_item(self.price_input)

        self.instructions_input = discord.ui.InputText(
            label="Specific Instructions", placeholder="Any specific instructions?", style=discord.InputTextStyle.long
        )
        self.add_item(self.instructions_input)

    async def callback(self, interaction: discord.Interaction):
        # Get the data from the modal
        price = self.price_input.value
        instructions = self.instructions_input.value
        user = interaction.user

        creationEmbed = discord.Embed(
            title="Ticket Created",
            description= (
                f"{user.mention} your ticket has been created! Our team will be with you as soon as possible.\n"
                f"**Reason**\n"
                f"Want to sell [Click here]({self.message_link})"
            ),
            color=discord.Color.green()
        )
        creationEmbed.set_footer(text="Ticket System")
        creationEmbed.timestamp = datetime.datetime.now()
        embed = discord.Embed(
            title="Ticket Created",
            description=(
                f"**Item:** {self.item_name}\n\n"
                f"**Price for {self.pricetype}:** {self.price} => {self.price_input.value}\n\n"
                f"**Payment:** {self.payment}\n\n"
                f"**Type:** {self.type}\n\n"
                f"**Specific:** {self.specific} => {self.instructions_input.value}\n\n"
                f"**Quantity:** {self.quantity}\n\n"
                f"**Collateral:** {self.collateral}\n\n"
                f"**Project Link:** {self.project_link}\n\n"

            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="Building trust in web3")
        embed.timestamp = datetime.datetime.now()

        await interaction.response.defer(ephemeral=True)

        # Get the category and channel where the tickets will be created
        category = discord.utils.get(interaction.guild.categories, name="Support Tickets")
        if category is None:
            await interaction.followup.send("The 'Tickets' category does not exist.", ephemeral=True)
            return

        # Create a new text channel with the name including user and item name
        channel_name = f"{user.name}-{self.item_name}".lower()
        mod_role = get(interaction.guild.roles, name="Middlemen")

        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites={
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
                mod_role: discord.PermissionOverwrite(read_messages=True, send_messages=True) if mod_role else None
            }
        )
        await channel.edit(topic=f"Refer to the original message here: {self.message_link}")

        mentions = [user.mention]
        mentions.append(f" <@&{moderator_role_id}>")
        mention_message = " ".join(mentions)
        await channel.send(mention_message)
        await channel.send(embed=creationEmbed, view=TicketButtonView(self.message_link, self.item_name, self.price_input, self.payment,self.type, self.specific,self.quantity, self.collateral, self.view_id))
        await channel.send(embed=embed)
        await interaction.followup.send(f"Your ticket has been created: {channel.mention}", ephemeral=True)

class QuickSellModal(discord.ui.Modal):
    def __init__(self, item_name, chain, pricetype, price, payment, type, specific, quantity, collateral, project_link, message_link, view_id):
        super().__init__(title="Confirm your order")
        self.item_name = item_name
        self.chain = chain
        self.pricetype = pricetype
        self.price = price
        self.payment = payment
        self.type = type
        self.specific = specific
        self.quantity = quantity
        self.collateral = collateral
        self.project_link = project_link
        self.message_link = message_link
        self.view_id = view_id

        self.message_input = discord.ui.InputText(
            label="Message", value="Are you sure you want to buy this item?",required=True, style=discord.InputTextStyle.short
        )
        self.add_item(self.message_input)

        self.instructions_input = discord.ui.InputText(
            label="Terms of Service",
            value="1. Spam tickets will be banned.\n"
                  "2. Opening tickets without reason will be deleted.\n"
                  "3. Be a smart customer.",
            style=discord.InputTextStyle.long,
            required=True,
        )
        self.add_item(self.instructions_input)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        creationEmbed = discord.Embed(
            title="Ticket Created",
            description= (
                f"{user.mention} your ticket has been created! Our team will be with you as soon as possible.\n"
                f"**Reason**\n"
                f"Want to sell [Click here]({self.message_link})"
            ),
            color=discord.Color.green()
        )
        creationEmbed.set_footer(text="Ticket System")
        creationEmbed.timestamp = datetime.datetime.now()


        embed = discord.Embed(
            title="Ticket Created",
            description=(
                f"**Item:** {self.item_name}\n\n"
                f"**Price for {self.pricetype}:** {self.price}\n\n"
                f"**Payment:** {self.payment}\n\n"
                f"**Type:** {self.type}\n\n"
                f"**Specific:** {self.specific}\n\n"
                f"**Quantity:** {self.quantity}\n\n"
                f"**Collateral:** {self.collateral}\n\n"
                f"**Project Link:** {self.project_link}\n\n"

            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="Building trust in web3")
        embed.timestamp = datetime.datetime.now()

        await interaction.response.defer(ephemeral=True)

        # Get the category and channel where the tickets will be created
        category = discord.utils.get(interaction.guild.categories, name="Support Tickets")
        if category is None:
            await interaction.followup.send("The 'Tickets' category does not exist.", ephemeral=True)
            return

        # Create a new text channel with the name including user and item name
        channel_name = f"{user.name}-{self.item_name}".lower()
        mod_role = get(interaction.guild.roles, name="Middlemen")

        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites={
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
                mod_role: discord.PermissionOverwrite(read_messages=True, send_messages=True) if mod_role else None
            }
        )
        await channel.edit(topic=f"Refer to the original message here: {self.message_link}")
        mentions = [user.mention]
        mentions.append(f" <@&{moderator_role_id}>")
        mention_message = " ".join(mentions)
        await channel.send(mention_message)
        await channel.send(embed=creationEmbed, view=TicketButtonView(self.message_link, self.item_name, self.price, self.payment,self.type, self.specific,self.quantity, self.collateral,self.view_id))
        await channel.send(embed=embed)

        # Confirm to the user that the ticket has been created
        await interaction.followup.send(f"Your ticket has been created: {channel.mention}", ephemeral=True)

class QuickBuyModal(discord.ui.Modal):
    def __init__(self, item_name, chain, pricetype, price, payment, type, specific, quantity, collateral, project_link, message_link, view_id):
        super().__init__(title="Confirm your order")
        self.item_name = item_name
        self.chain = chain
        self.pricetype = pricetype
        self.price = price
        self.payment = payment
        self.type = type
        self.specific = specific
        self.quantity = quantity
        self.collateral = collateral
        self.project_link = project_link
        self.message_link = message_link
        self.view_id = view_id

        self.message_input = discord.ui.InputText(
            label="Message", value="Are you sure you want to buy this item?",required=True, style=discord.InputTextStyle.short
        )
        self.add_item(self.message_input)

        self.instructions_input = discord.ui.InputText(
            label="Terms of Service",
            value="1. Spam tickets will be banned.\n"
                  "2. Opening tickets without reason will be deleted.\n"
                  "3. Be a smart customer.",
            style=discord.InputTextStyle.long,
            required=True,
        )
        self.add_item(self.instructions_input)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user

        creationEmbed = discord.Embed(
            title="Ticket Created",
            description= (
                f"{user.mention} your ticket has been created! Our team will be with you as soon as possible.\n"
                f"**Reason**\n"
                f"Want to sell [Click here]({self.message_link})"
            ),
            color=discord.Color.green()
        )
        creationEmbed.set_footer(text="Ticket System")
        creationEmbed.timestamp = datetime.datetime.now()


        embed = discord.Embed(
            title="Ticket Created",
            description=(
                f"**Item:** {self.item_name}\n\n"
                f"**Price for {self.pricetype}:** {self.price}\n\n"
                f"**Payment:** {self.payment}\n\n"
                f"**Type:** {self.type}\n\n"
                f"**Specific:** {self.specific}\n\n"
                f"**Quantity:** {self.quantity}\n\n"
                f"**Collateral:** {self.collateral}\n\n"
                f"**Project Link:** {self.project_link}\n\n"

            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="Building trust in web3")
        embed.timestamp = datetime.datetime.now()

        await interaction.response.defer(ephemeral=True)
        category = discord.utils.get(interaction.guild.categories, name="Support Tickets")
        if category is None:
            await interaction.followup.send("The 'Tickets' category does not exist.", ephemeral=True)
            return

        channel_name = f"{user.name}-{self.item_name}".lower()

        mod_role = get(interaction.guild.roles, name="Middlemen")

        channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites={
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
                mod_role: discord.PermissionOverwrite(read_messages=True, send_messages=True) if mod_role else None
            }
        )


        await channel.edit(topic=f"Refer to the original message here: {self.message_link}")


        

        mentions = [user.mention]
        mentions.append(f" <@&{moderator_role_id}>")
        mention_message = " ".join(mentions)
        await channel.send(mention_message)
        await channel.send(embed=creationEmbed, view=TicketButtonView(self.message_link, self.item_name, self.price, self.payment,self.type, self.specific,self.quantity, self.collateral, self.view_id))
        await channel.send(embed=embed)

        await interaction.followup.send(f"Your ticket has been created: {channel.mention}", ephemeral=True)


class SellButtonView(discord.ui.View):
    def __init__(self, item_name, chain, pricetype, price, payment, type, specific, quantity, collateral, project_link, message_link=None, user=None, view_id=None,view_type="sell",):
        super().__init__(timeout=None)
        self.item_name = item_name
        self.chain = chain
        self.pricetype = pricetype
        self.price = price
        self.payment = payment
        self.type = type
        self.specific = specific
        self.quantity = quantity
        self.collateral = collateral
        self.project_link  = project_link
        self.message_link = message_link
        self.user = user
        self.view_id = view_id or str(uuid.uuid4())
        self.view_type = view_type

    
    def to_dict(self):
        return {
            "view_id": self.view_id,
            "item_name": self.item_name,
            "chain": self.chain,
            "pricetype": self.pricetype,
            "price": self.price,
            "payment": self.payment,
            "type": self.type,
            "specific": self.specific,
            "quantity": self.quantity,
            "collateral": self.collateral,
            "project_link": self.project_link,
            "message_link": self.message_link,
            "user_id": self.user.id if self.user else None,
            "view_type": self.view_type,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            item_name=data['item_name'],
            chain=data['chain'],
            pricetype=data['pricetype'],
            price=data['price'],
            payment=data['payment'],
            type=data['type'],
            specific=data['specific'],
            quantity=data['quantity'],
            collateral=data['collateral'],
            project_link=data['project_link'],
            message_link=data.get('message_link'),
            user=None,  # This can be fetched separately using user_id if needed
            view_id=data['view_id'],
            view_type=data.get('view_type', 'sell')
        )


    @discord.ui.button(label="Make Offer", style=discord.ButtonStyle.primary, custom_id="make_offer")
    async def make_offer(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(MakeOfferSellModal(self.item_name, self.chain, self.pricetype, self.price, self.payment, self.type, self.specific, self.quantity, self.collateral, self.project_link, self.message_link, self.view_id))

    @discord.ui.button(label="Quick Buy", style=discord.ButtonStyle.success, custom_id="quick_buy")
    async def quick_buy(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(QuickBuyModal(self.item_name, self.chain, self.pricetype, self.price, self.payment, self.type, self.specific, self.quantity, self.collateral, self.project_link,  self.message_link, self.view_id))

    @discord.ui.button(label="Delist", style=discord.ButtonStyle.danger, custom_id="delist")
    async def delist(self, button: discord.ui.Button, interaction: discord.Interaction):
        if any(role.id in allowed_roles for role in interaction.user.roles):
            if self.message_link:
                try:
                    guild_id, channel_id, message_id = self.message_link.split('/')[-3:]
                    channel = interaction.guild.get_channel(int(channel_id))
                    if channel:
                        message = await channel.fetch_message(int(message_id))
                        await message.delete()
                        await interaction.response.send_message("The listing has been successfully delisted.", ephemeral=True)
                        if self.view_id:
                            print(self.view_id)
                            delete_view_from_db(self.view_id)
                            print(f"Deleted view with ID {self.view_id} from the database.")
                    else:
                        await interaction.response.send_message("Could not find the channel to delist the item.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"An error occurred while trying to delist the item: {e}", ephemeral=True)
            else:
                await interaction.response.send_message("No message link found to delist the item.", ephemeral=True)
        else:
            await interaction.response.send_message("You do not have sufficient permissions", ephemeral=True)

    @discord.ui.button(label="👁️ View Seller", style=discord.ButtonStyle.secondary, custom_id="view_seller")
    async def view_seller(self, button: discord.ui.Button, interaction: discord.Interaction):
        if any(role.id in allowed_roles for role in interaction.user.roles):
            user = self.user 
            guild = interaction.guild  
            member = guild.get_member(user.id) if guild else None  

        
            embed = discord.Embed(title="Seller Information", color=discord.Color.blue())
            embed.add_field(name="Username", value=f"{user.name}#{user.discriminator}", inline=True)
            embed.add_field(name="User ID", value=user.id, inline=True)
            embed.add_field(name="Account Created On", value=user.created_at.strftime("%Y-%m-%d"), inline=True)

            if member:  
                embed.add_field(name="Status", value=member.status, inline=True)
                embed.add_field(name="Server Nickname", value=member.nick or "None", inline=True)
                embed.add_field(name="Joined Server On", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)

                roles = [role.mention for role in member.roles if role.name != "@everyone"]
                embed.add_field(name="Roles", value=", ".join(roles) if roles else "No Roles", inline=False)

            embed.set_thumbnail(url=user.avatar.url)  
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("You do not have sufficient permissions", ephemeral=True)


class BuyButtonView(discord.ui.View):
    def __init__(self, item_name, chain, pricetype, price, payment, type, specific, quantity, collateral, project_link, message_link= None, user=None, view_id=None,view_type="buy",):
        super().__init__(timeout=None)
        self.item_name = item_name
        self.chain = chain
        self.pricetype = pricetype
        self.price = price
        self.payment = payment
        self.type = type
        self.specific = specific
        self.quantity = quantity
        self.collateral = collateral
        self.project_link  = project_link
        self.message_link = message_link
        self.user = user
        self.view_id = view_id or str(uuid.uuid4())
        self.view_type = view_type
    
    
    def to_dict(self):
        return {
            "view_id": self.view_id,
            "item_name": self.item_name,
            "chain": self.chain,
            "pricetype": self.pricetype,
            "price": self.price,
            "payment": self.payment,
            "type": self.type,
            "specific": self.specific,
            "quantity": self.quantity,
            "collateral": self.collateral,
            "project_link": self.project_link,
            "message_link": self.message_link,
            "user_id": self.user.id if self.user else None,
            "view_type": self.view_type,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            item_name=data['item_name'],
            chain=data['chain'],
            pricetype=data['pricetype'],
            price=data['price'],
            payment=data['payment'],
            type=data['type'],
            specific=data['specific'],
            quantity=data['quantity'],
            collateral=data['collateral'],
            project_link=data['project_link'],
            message_link=data.get('message_link'),
            user=None,  # This can be fetched separately using user_id if needed
            view_id=data['view_id'],
            view_type=data.get('view_type', 'buy')
        )

    @discord.ui.button(label="Make Offer", style=discord.ButtonStyle.primary, custom_id="make_offer")
    async def make_offer(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(MakeOfferBuyModal(self.item_name, self.chain, self.pricetype, self.price, self.payment, self.type, self.specific, self.quantity, self.collateral, self.project_link,self.message_link, self.view_id))

    @discord.ui.button(label="Quick Sell", style=discord.ButtonStyle.success, custom_id="quick_sell")
    async def quick_sell(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(QuickSellModal(self.item_name, self.chain, self.pricetype, self.price, self.payment, self.type, self.specific, self.quantity, self.collateral, self.project_link, self.message_link, self.view_id))

    @discord.ui.button(label="Delist", style=discord.ButtonStyle.danger, custom_id="delist")
    async def delist(self, button: discord.ui.Button, interaction: discord.Interaction):
        if any(role.id in allowed_roles for role in interaction.user.roles):
            if self.message_link:
                try:
                    guild_id, channel_id, message_id = self.message_link.split('/')[-3:]
                    channel = interaction.guild.get_channel(int(channel_id))
                    if channel:
                        message = await channel.fetch_message(int(message_id))
                        await message.delete()
                        await interaction.response.send_message("The listing has been successfully delisted.", ephemeral=True)
                        if self.view_id:
                            delete_view_from_db(self.view_id)
                            print(f"Deleted view with ID {self.view_id} from the database.")
                    else:
                        await interaction.response.send_message("Could not find the channel to delist the item.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"An error occurred while trying to delist the item: {e}", ephemeral=True)
            else:
                await interaction.response.send_message("No message link found to delist the item.", ephemeral=True)
        else:
            await interaction.response.send_message("You do not have sufficient permissions", ephemeral=True)

    @discord.ui.button(label="👁️ View Seller", style=discord.ButtonStyle.secondary, custom_id="view_seller")
    async def view_seller(self, button: discord.ui.Button, interaction: discord.Interaction):
        if any(role.id in allowed_roles for role in interaction.user.roles):
            user = self.user  
            guild = interaction.guild  
            member = guild.get_member(user.id) if guild else None  

            
            embed = discord.Embed(title="Seller Information", color=discord.Color.blue())
            embed.add_field(name="Username", value=f"{user.name}#{user.discriminator}", inline=True)
            embed.add_field(name="User ID", value=user.id, inline=True)
            embed.add_field(name="Account Created On", value=user.created_at.strftime("%Y-%m-%d"), inline=True)

            if member:  
                embed.add_field(name="Status", value=member.status, inline=True)
                embed.add_field(name="Server Nickname", value=member.nick or "None", inline=True)
                embed.add_field(name="Joined Server On", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
                roles = [role.mention for role in member.roles if role.name != "@everyone"]
                embed.add_field(name="Roles", value=", ".join(roles) if roles else "No Roles", inline=False)

            embed.set_thumbnail(url=user.avatar.url)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("You do not have sufficient permissions", ephemeral=True)

class ConfirmSellView(discord.ui.View):
    def __init__(self, embed, view: SellButtonView):
        super().__init__()
        self.embed = embed
        self.sell_view = view 

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        user = interaction.user
        await interaction.response.edit_message(content="Your listing has been posted!", embed=None, view=None)
       
        message = await interaction.channel.send(embed=self.embed, view=self.sell_view)
        guild_id = interaction.guild.id
        channel_id = interaction.channel.id
        message_id = message.id
        message_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
        self.sell_view.message_link = message_link
        self.sell_view.user = user

        # Convert SellButtonView to a dictionary for saving
        data = self.sell_view.to_dict()
        save_view(data)  # Save the data in MongoDB

        print("SellButtonView data saved to MongoDB:", data)

class ConfirmBuyView(discord.ui.View):
    def __init__(self, embed, view:BuyButtonView):
        super().__init__(timeout=None)
        self.embed = embed
        self.buy_view = view 

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        user = interaction.user
        await interaction.response.edit_message(content="Your listing has been posted!", embed=None, view=None)
       
        message = await interaction.channel.send(embed=self.embed, view=self.buy_view)
        guild_id = interaction.guild.id
        channel_id = interaction.channel.id
        message_id = message.id
        message_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
        self.buy_view.message_link = message_link
        self.buy_view.user = user
        
        # Convert SellButtonView to a dictionary for saving
        data = self.buy_view.to_dict()
        save_view(data)  # Save the data in MongoDB

        print("BuyButtonView data saved to MongoDB:", data)

class TicketButtonView(discord.ui.View):
    def __init__(self, message_link=None, item_name=None, price_input = None,payment=None, type=None, specific = None,quantity=None,collateral=None, view_id = None):
        super().__init__(timeout=None)
        self.message_link = message_link
        self.item_name = item_name
        self.price_input =price_input 
        self.payment = payment
        self.type = type
        self.specific = specific
        self.quantity = quantity
        self.collateral = collateral
        self.view_id = view_id

    
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.primary, custom_id="close_ticket")
    async def make_offer(self, button: discord.ui.Button, interaction: discord.Interaction):
        if any(role.id in allowed_roles for role in interaction.user.roles):
            await interaction.response.send_message("Closing the ticket...", ephemeral=True)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("You do not have permission to close this ticket.", ephemeral=True)

    @discord.ui.button(label="View Buyer", style=discord.ButtonStyle.success, custom_id="view_buyer")
    async def quick_buy(self, button: discord.ui.Button, interaction: discord.Interaction):
        if any(role.id in allowed_roles for role in interaction.user.roles):
            await interaction.response.send_message("View Buyer", ephemeral=True)
        else:
            await interaction.response.send_message("You do not have sufficient permissions", ephemeral=True)

    @discord.ui.button(label="Mark as Sold", style=discord.ButtonStyle.danger, custom_id="mark_as_sold")
    async def mark_as_sold(self, button: discord.ui.Button, interaction: discord.Interaction):
        print(self.view_id)
        if any(role.id in allowed_roles for role in interaction.user.roles):
            if self.message_link:
                try:
                    
                    guild_id, channel_id, message_id = self.message_link.split('/')[-3:]
                    channel = interaction.guild.get_channel(int(channel_id))
                    if channel:
                        original_message = await channel.fetch_message(int(message_id))

                        sold_out_view = discord.ui.View()
                        sold_out_button = discord.ui.Button(label="Sold Out", style=discord.ButtonStyle.danger, disabled=True)
                        sold_out_view.add_item(sold_out_button)
                        await original_message.edit(view=sold_out_view)
                        await interaction.response.send_message("The item has been marked as sold, and the original listing has been updated.", ephemeral=True)
                        embed = discord.Embed( color=discord.Color.red())
                        embed.add_field(name="Item Name", value=self.item_name, inline=True)
                        price = self.price_input.value if isinstance(self.price_input, discord.ui.TextInput) else self.price_input
                        price_with_payment = f"{price} {self.payment}"
                        embed.add_field(name="Price", value=price_with_payment, inline=True)
                        embed.add_field(name="Type", value=self.type, inline=True)
                        embed.add_field(name="Specifics", value=self.specific, inline=True)
                        embed.add_field(name="Quantity", value=self.quantity, inline=True)
                        embed.add_field(name="Collateral", value=self.collateral, inline=True)
                        embed.add_field(name="Middleman", value=interaction.user.mention, inline=True)

                        
                        CHANNEL_ID = 1300149511754088548
                        recent_sales_channel = interaction.guild.get_channel(CHANNEL_ID)
                        if recent_sales_channel:
                            await recent_sales_channel.send(embed=embed)
                        else:
                            await interaction.followup.send("The recent-sales channel could not be found.", ephemeral=True)
                        if self.view_id:
                            delete_view_from_db(self.view_id)
                            print(f"Deleted view with ID {self.view_id} from the database.")
                    else:
                        await interaction.response.send_message("Could not find the channel for the original listing.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"An error occurred while trying to mark the item as sold: {e}", ephemeral=True)

            else:
                await interaction.response.send_message("No link to the original message was found.", ephemeral=True)
        else:
            await interaction.response.send_message("You do not have sufficient permissions", ephemeral=True)

    @discord.ui.button(label="Create Invoice", style=discord.ButtonStyle.secondary, custom_id="create_invoice")
    async def view_seller(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True) 

        
        transcript = await chat_exporter.export(
            channel=interaction.channel,
            limit=None,  
            tz_info="UTC",  
            military_time=True,  
            bot=interaction.client,  
        )

        if transcript is None:
            await interaction.followup.send("Failed to generate the invoice. No messages found in the channel.", ephemeral=True)
            return

        transcript_file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"invoice-{interaction.channel.name}.html",
        )
        await interaction.user.send(content="Here is your invoice:", file=transcript_file)
        await interaction.followup.send("The invoice has been sent to your DMs!", ephemeral=True)

        





@bot.slash_command(name="sell", description="List an item for sale")
@commands.cooldown(1, 3, commands.BucketType.user)
async def sell(
    ctx: discord.ApplicationContext,
    name:str= discord.Option(str, "Name of NFT"),
    chain: str = discord.Option(description="The Blockchain", choices=["Solana", "Bitcoin", "Ethereum", "Zksync", "Base", "Polygon", "Injective", "SUI", "None"]),
    price:str= discord.Option(float, "The Price of the NFT"),
    pricetype: str = discord.Option(description="Pricing type", choices=["All", "Each"]),
    payment: str = discord.Option(description="Payment method", choices=["SOL", "USD"]),
    specific:str= discord.Option(str, "Specific Instructions"),
    type: str = discord.Option(description="Type of Transaction", choices=["Discord Surrender", "Wallet Surrender", "Wallet Submit", "Mint", "Code", "Any"]),
    quantity: int = discord.Option(str, "Specify the Quantity"),
    collateral: str = discord.Option(description="Is collateral required?", choices=["Yes", "No"]),
    offer: str = discord.Option(description="Is this an offer?", choices=["Yes", "No"]),
    project_link: str = discord.Option(str, "Link to the project"),
):
    embed = discord.Embed(
        description=(
            f"**Item:** {name}\n\n"
            f"**Chain:** {chain}\n\n"
            f"**Price for {pricetype}:** {price}\n\n"
            f"**Payment:** {payment}\n\n"
            f"**Type:** {type}\n\n"
            f"**Specific:** {specific}\n\n"
            f"**Quantity:** {quantity}\n\n"
            f"**Collateral:** {collateral}\n\n"
            f"**Project Link:** {project_link}\n\n"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="Building trust in web3")  
    embed.timestamp = datetime.datetime.now()
    
    
    view=ConfirmSellView(embed=embed, view= SellButtonView(name, chain, pricetype, price, payment, type, specific, quantity, collateral, project_link))
    await ctx.respond(embed=embed, view=view, ephemeral=True)


@bot.slash_command(name="buy", description="List an item for buy")
@commands.cooldown(1, 3, commands.BucketType.user)
async def sell(
    ctx: discord.ApplicationContext,
    name:str= discord.Option(str, "Name of NFT"),
    chain: str = discord.Option(description="The Blockchain", choices=["Solana", "Bitcoin", "Ethereum", "Zksync", "Base", "Polygon", "Injective", "SUI", "None"]),
    price:str= discord.Option(float, "The Price of the NFT"),
    pricetype: str = discord.Option(description="Pricing type", choices=["All", "Each"]),
    payment: str = discord.Option(description="Payment method", choices=["SOL", "USD"]),
    specific:str= discord.Option(str, "Specific Instructions"),
    type: str = discord.Option(description="Type of Transaction", choices=["Discord Surrender", "Wallet Surrender", "Wallet Submit", "Mint", "Code", "Any"]),
    quantity: int = discord.Option(str, "Specify the Quantity"),
    collateral: str = discord.Option(description="Is collateral required?", choices=["Yes", "No"]),
    offer: str = discord.Option(description="Is this an offer?", choices=["Yes", "No"]),
    project_link: str = discord.Option(str, "Link to the project"),
):
    embed = discord.Embed(
        description=(
            f"**Item:** {name}\n\n"
            f"**Chain:** {chain}\n\n"
            f"**Price for {pricetype}:** {price}\n\n"
            f"**Payment:** {payment}\n\n"
            f"**Type:** {type}\n\n"
            f"**Specific:** {specific}\n\n"
            f"**Quantity:** {quantity}\n\n"
            f"**Collateral:** {collateral}\n\n"
            f"**Project Link:** {project_link}\n\n"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="Building trust in web3")  
    embed.timestamp = datetime.datetime.now()
    
    
    view=ConfirmBuyView(embed=embed, view= BuyButtonView(name, chain, pricetype, price, payment, type, specific, quantity, collateral, project_link))
    await ctx.respond(embed=embed, view=view, ephemeral=True)

class TicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Create Ticket", style=discord.ButtonStyle.primary, custom_id="create_ticket")

    async def callback(self, interaction: discord.Interaction):
        category = discord.utils.get(interaction.guild.categories, name="Support Tickets")
        
        if category is None:
            await interaction.response.send_message("Support ticket category not found.", ephemeral=True)
            return
        
        channel_name = f"support-{interaction.user.name}"
        mod_role = get(interaction.guild.roles, name="Middlemen")

        ticket_channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites={
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
                mod_role: discord.PermissionOverwrite(read_messages=True, send_messages=True) if mod_role else None
            }
        )
        
        await interaction.response.send_message(f"Your support ticket has been created: {ticket_channel.mention}", ephemeral=True)
        
        
        await ticket_channel.send(f"Hello {interaction.user.mention}, a member of our support team will be with you shortly.")

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketButton())

@bot.slash_command(name="setup_ticket", description="Set up the ticket system in this channel")
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="Meta Support",
        description="Open the ticket for support, queries & feedback.\n❗️Please don't spam, abuse or violate any community guidelines❗️ ",
        color=discord.Color.blue()
    )
    
    await ctx.send(embed=embed, view=TicketView())



bot.run(bot_token)