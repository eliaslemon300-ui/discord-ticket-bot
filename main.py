import discord
from discord.ext import commands
from discord import app_commands, Interaction, SelectOption
import os

# 🔐 Token from environment variable
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# ⚙️ IDs
GUILD_ID = 1394312686090715248
FREE_ROLE_ID = 1395166044762542222
PREMIUM_ROLE_ID = 1395166045974560829
JOIN_ROLE_ID = 1395166065675337760

# Ticket Zähler
ticket_counter = 0

# Intents
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Dropdown zum Ticket-Erstellen ---
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            SelectOption(label="BuyCoins", description="Buy FUT coins"),
            SelectOption(label="General Help", description="Ask general questions"),
            SelectOption(label="Bug Report", description="Report a bug"),
            SelectOption(label="Partnership", description="Partner with us"),
        ]
        super().__init__(placeholder="📩 Choose a ticket category", options=options)

    async def callback(self, interaction: Interaction):
        global ticket_counter
        user = interaction.user
        category_name = self.values[0]

        ticket_counter += 1
        ticket_name = f"ticket-{ticket_counter:03d}"

        guild = interaction.guild

        # Berechtigungen
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True),
            guild.get_role(PREMIUM_ROLE_ID): discord.PermissionOverwrite(view_channel=True),
        }

        # Kategorie erstellen oder holen
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(name=category_name, overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False)
            })

        # Ticket-Channel erstellen
        ticket_channel = await guild.create_text_channel(name=ticket_name, overwrites=overwrites, category=category)

        # Embed im Ticket
        embed = discord.Embed(title=f"📩 New Ticket - {category_name}", color=0x00ff00)
        if category_name == "BuyCoins":
            embed.description = "Please provide your **account name**, **platform**, **coin amount** and backup codes (if needed)."
        else:
            embed.description = f"Hello {user.mention}, our support will assist you shortly."

        embed.set_footer(text="Click the 🔒 button to close this ticket.")

        view = CloseButton()
        await ticket_channel.send(content=f"{user.mention} <@&{PREMIUM_ROLE_ID}>", embed=embed, view=view)

        # Log Channel finden oder erstellen
        log_name = "ticket-support-premium" if PREMIUM_ROLE_ID in [r.id for r in user.roles] else "ticket-support"
        log_channel = discord.utils.get(guild.text_channels, name=log_name)
        if not log_channel:
            logs_category = discord.utils.get(guild.categories, name="Logs")
            if not logs_category:
                logs_category = await guild.create_category("Logs")
            log_channel = await guild.create_text_channel(log_name, category=logs_category)

        await log_channel.send(f"📨 {user.mention} opened `{category_name}` ticket: {ticket_channel.mention}")
        await interaction.response.send_message(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)

# --- Close Button ---
class CloseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket 🔒", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

# --- Beim Start: Dropdown-Panel automatisch senden ---
@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Bot is ready: {bot.user}")

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return

    channel = discord.utils.get(guild.text_channels, name="create-ticket")
    if not channel:
        tickets_cat = discord.utils.get(guild.categories, name="Tickets") or await guild.create_category("Tickets")
        channel = await guild.create_text_channel("create-ticket", category=tickets_cat)

    await channel.purge(limit=5)
    view = discord.ui.View()
    view.add_item(TicketDropdown())

    embed = discord.Embed(
        title="🎫 Create a Ticket",
        description="Select a category below to open a private support ticket.",
        color=discord.Color.blurple()
    )

    await channel.send(embed=embed, view=view)

# --- Join-Event: Automatisch Rolle geben ---
@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, id=JOIN_ROLE_ID)
    if role:
        await member.add_roles(role)
        print(f"👤 Assigned join role to {member.name}")

# --- Slash Command: /help ---
@bot.tree.command(name="help", description="Show help")
async def help_command(interaction: Interaction):
    await interaction.response.send_message("Use `/ticket` or go to #create-ticket to open a support ticket.", ephemeral=True)

# --- Slash Command: /close ---
@bot.tree.command(name="close", description="Close this ticket")
async def close_command(interaction: Interaction):
    await interaction.channel.delete()

bot.run(TOKEN)
