import discord
from discord.ext import commands
from discord import app_commands
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1394312686090715248
ADMIN_ROLE_ID = 1395160172695130152
JOIN_ROLE_ID = 1395166044762542222
PREMIUM_ROLE_ID = 1395166045974560829
TICKET_PANEL_CHANNEL_ID = 1395166065675337760

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_member_join(member):
    role = member.guild.get_role(JOIN_ROLE_ID)
    if role:
        await member.add_roles(role)
        print(f"Assigned {role.name} to {member.name}")


@bot.event
async def on_ready():
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Bot is online as {bot.user}")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(TICKET_PANEL_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="📩 Open a Ticket",
            description="Select a category below to create a support ticket.",
            color=0x5865F2
        )
        await channel.purge(limit=1)
        await channel.send(embed=embed, view=TicketDropdownView())


@bot.tree.command(name="ticket", description="Open a support ticket", guild=discord.Object(id=GUILD_ID))
async def ticket_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📩 Open a Ticket",
        description="Select a category from the menu below.",
        color=0x5865F2
    )
    await interaction.response.send_message(embed=embed, view=TicketDropdownView(), ephemeral=True)


@bot.tree.command(name="help", description="Show help commands", guild=discord.Object(id=GUILD_ID))
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Bot Commands",
        description="/ticket – Open a support ticket\n/help – Show this help message",
        color=0x3498db
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())


class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="💸 Buy Coins", value="buy_coins", description="Buy coins or currency"),
            discord.SelectOption(label="⚙️ General Help", value="general", description="Ask general questions"),
            discord.SelectOption(label="🛠 Bug Report", value="bug", description="Report a bug"),
            discord.SelectOption(label="🤝 Partnership", value="partner", description="Request a partnership"),
        ]
        super().__init__(placeholder="Select ticket category...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "buy_coins":
            await interaction.response.send_modal(BuyCoinsForm())
        else:
            await create_ticket(interaction, self.values[0])


class BuyCoinsForm(discord.ui.Modal, title="💸 Buy Coins – Provide EA Account Info"):
    email = discord.ui.TextInput(label="EA Email", required=True)
    password = discord.ui.TextInput(label="EA Password", required=True, style=discord.TextStyle.short)
    platform = discord.ui.TextInput(label="Platform (e.g. PS, Xbox, PC)", required=True)
    coins = discord.ui.TextInput(label="Coins Amount", required=True)
    backup = discord.ui.TextInput(label="Backup Codes", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        content = (
            f"📝 **New Coin Order**\n\n"
            f"**EA Email:** {self.email}\n"
            f"**EA Password:** {self.password}\n"
            f"**Platform:** {self.platform}\n"
            f"**Coins Requested:** {self.coins}\n"
            f"**Backup Codes:** {self.backup}\n\n"
            f"⚠️ This info is private. Only you and our verified support team can see this."
        )
        await create_ticket(interaction, "buy_coins", content)


async def create_ticket(interaction, category_key, extra_message=None):
    category_map = {
        "buy_coins": "💸 BuyCoins",
        "general": "⚙️ General",
        "bug": "🛠 BugReports",
        "partner": "🤝 Partnerships"
    }

    guild = interaction.guild
    user = interaction.user

    # Create category if not exists
    cat_name = category_map.get(category_key, "📁 Tickets")
    discord_category = discord.utils.get(guild.categories, name=cat_name)
    if not discord_category:
        discord_category = await guild.create_category(name=cat_name)

    # Premium check
    is_premium = PREMIUM_ROLE_ID in [role.id for role in user.roles]
    ticket_name = f"premium-{user.name}" if is_premium else f"ticket-{user.name}"
    ticket_name = ticket_name.lower().replace(" ", "-")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.get_role(ADMIN_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    channel = await guild.create_text_channel(
        name=ticket_name,
        category=discord_category,
        overwrites=overwrites
    )

    embed = discord.Embed(
        title=f"🎫 Ticket: {cat_name}",
        description="Please wait for a staff member. You can close this ticket anytime with the 🔒 button.",
        color=0x00ffcc
    )
    embed.set_footer(text=f"Opened by {user}", icon_url=user.display_avatar.url)

    await channel.send(content=f"<@&{ADMIN_ROLE_ID}>\n{extra_message or ''}", embed=embed, view=CloseTicketView())
    await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

    # Log
    log_channel = discord.utils.get(guild.text_channels, name="ticket-logs")
    if log_channel:
        await log_channel.send(f"📥 Ticket created by {user.mention} in category `{cat_name}` → {channel.mention}")


class CloseTicketView(discord.ui.View):
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = discord.utils.get(interaction.guild.text_channels, name="ticket-logs")
        if log_channel:
            await log_channel.send(f"📤 Ticket closed: {interaction.channel.name} by {interaction.user.mention}")
        await interaction.channel.delete()


bot.run(TOKEN)
