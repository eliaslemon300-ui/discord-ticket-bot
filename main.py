import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1394312686090715248
JOIN_ROLE = 1395166044762542222
ADMIN_ROLE_ID = 1395160172695130152
FREE_ROLE_ID = 1395166044762542222
PREMIUM_ROLE_ID = 1395166045974560829

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Buy Coins", description="Order coins now"),
            discord.SelectOption(label="General Help", description="Ask general questions"),
            discord.SelectOption(label="Bug Report", description="Report an issue or bug"),
            discord.SelectOption(label="Partnership", description="Request a partnership")
        ]
        super().__init__(placeholder="📩 Select a ticket category", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category_name = self.values[0].replace(" ", "")
        guild = interaction.guild

        if self.values[0] == "Buy Coins":
            form_fields = "Please provide the following:\n- Your EA Account Email\n- Platform\n- Coin Amount\n- Backup Codes (if available)"
        else:
            form_fields = "Please describe your issue or request in detail."

        # Check if user has premium role
        is_premium = PREMIUM_ROLE_ID in [role.id for role in interaction.user.roles]
        is_free = FREE_ROLE_ID in [role.id for role in interaction.user.roles]

        if is_premium:
            category = discord.utils.get(guild.categories, name=f"{category_name}Premium")
            log_channel = discord.utils.get(guild.text_channels, name="ticket-support-premium")
        else:
            category = discord.utils.get(guild.categories, name=category_name)
            log_channel = discord.utils.get(guild.text_channels, name="ticket-support")

        if category is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.get_role(ADMIN_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            category = await guild.create_category(category_name if not is_premium else f"{category_name}Premium", overwrites=overwrites)

        channel = await category.create_text_channel(name=f"ticket-{interaction.user.name}")

        await channel.send(
            f"🎫 Ticket opened by {interaction.user.mention}\n\n**Category:** {self.values[0]}\n\n{form_fields}",
            view=CloseTicketView()
        )

        if log_channel:
            await log_channel.send(f"📨 Ticket created by {interaction.user.mention}: {channel.mention}")

        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="❌ Close Ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")
    guild = bot.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.text_channels, name="create-ticket")
    if channel:
        await channel.purge(limit=10)
        await channel.send(embed=discord.Embed(
            title="Need Help? 🎟️",
            description="Select a category to create a support ticket.",
            color=discord.Color.blurple()
        ), view=TicketView())

@bot.event
async def on_member_join(member):
    if member.guild.id == GUILD_ID:
        role = member.guild.get_role(JOIN_ROLE)
        if role:
            await member.add_roles(role)
            print(f"👤 Assigned role {role.name} to {member.name}")

@bot.tree.command(name="ticket", description="Send the ticket menu again")
async def ticket_command(interaction: discord.Interaction):
    await interaction.response.send_message("Select a category to create a support ticket:", view=TicketView(), ephemeral=True)

@bot.tree.command(name="close", description="Close the current ticket channel")
async def close_command(interaction: discord.Interaction):
    await interaction.channel.delete()

@bot.tree.command(name="help", description="Show help info")
async def help_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Commands:**\n"
        "`/ticket` – Show the ticket menu\n"
        "`/close` – Close the current ticket\n"
        "`/help` – Show this message",
        ephemeral=True
    )

bot.run(TOKEN)
