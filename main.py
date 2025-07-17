import discord
from discord.ext import commands
from discord import app_commands
import os

TOKEN = os.getenv("TOKEN")
GUILD_ID = 1394312686090715248
ADMIN_ROLE_ID = 1395160172695130152
JOIN_ROLE_ID = 1395166044762542222
TICKET_CATEGORY_NAME = "🎟 Tickets"
TICKET_PANEL_CHANNEL_ID = 1395166065675337760  # Ticket panel channel (auto-message target)

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ Auto role on member join
@bot.event
async def on_member_join(member):
    role = member.guild.get_role(JOIN_ROLE_ID)
    if role:
        await member.add_roles(role)
        print(f"Assigned {role.name} to {member.name}")

# ✅ Auto-Dropdown message on ready
@bot.event
async def on_ready():
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Bot is online as {bot.user}")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

    # Send dropdown panel
    guild = bot.get_guild(GUILD_ID)
    channel = guild.get_channel(TICKET_PANEL_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="📩 Open a Ticket",
            description="Select a category from the dropdown below to get help.",
            color=0x5865F2
        )
        await channel.purge(limit=1)  # optional: clears old message
        await channel.send(embed=embed, view=TicketDropdownView())

# ✅ /ticket (manual fallback)
@bot.tree.command(name="ticket", description="Open a support ticket", guild=discord.Object(id=GUILD_ID))
async def ticket_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📩 Open a Ticket",
        description="Select a category from the menu below.",
        color=0x5865F2
    )
    await interaction.response.send_message(embed=embed, view=TicketDropdownView(), ephemeral=True)

# ✅ /help command
@bot.tree.command(name="help", description="Show bot commands", guild=discord.Object(id=GUILD_ID))
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Bot Commands",
        description="/ticket – Create a support ticket\n/help – Show this help menu",
        color=0x3498db
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ✅ Dropdown View + Ticket Creation
class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="💸 Buy Coins", value="Buy Coins", description="Buy coins or in-game currency"),
            discord.SelectOption(label="⚙️ General Help", value="General Help", description="Ask general questions"),
            discord.SelectOption(label="🛠 Bug Report", value="Bug Report", description="Report bugs or issues"),
            discord.SelectOption(label="🤝 Partnership", value="Partnership", description="Request a partnership"),
        ]
        super().__init__(placeholder="Select a ticket category...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(name=TICKET_CATEGORY_NAME)

        ticket_name = f"ticket-{interaction.user.name}".lower().replace(" ", "-")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(ADMIN_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=ticket_name,
            overwrites=overwrites,
            category=category
        )

        embed = discord.Embed(
            title=f"🎫 Ticket: {self.values[0]}",
            description="Thank you! An admin will assist you shortly.\nClick the 🔒 button below to close this ticket.",
            color=0x00ffcc
        )
        embed.set_footer(text=f"Opened by {interaction.user}", icon_url=interaction.user.display_avatar.url)

        await channel.send(content=f"<@&{ADMIN_ROLE_ID}>", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

# ✅ Close button
class CloseTicketView(discord.ui.View):
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

bot.run(TOKEN)
