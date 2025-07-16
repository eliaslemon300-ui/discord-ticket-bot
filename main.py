import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")  # Bot-Token kommt über Railway-Variable
GUILD_ID = 1394312686090715248
ADMIN_ROLE = 1395160172695130152
JOIN_ROLE = 1395166044762542222

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')

@bot.event
async def on_member_join(member):
    if member.guild.id == GUILD_ID:
        role = member.guild.get_role(JOIN_ROLE)
        if role:
            await member.add_roles(role)
            print(f'Assigned role {role.name} to {member.name}')

@bot.command()
@commands.has_role(ADMIN_ROLE)
async def setup_ticket(ctx):
    button = discord.ui.Button(label="📩 Create Ticket", style=discord.ButtonStyle.primary, custom_id="ticket_button")
    view = discord.ui.View()
    view.add_item(button)

    async def button_callback(interaction):
        guild = interaction.guild
        num = sum(1 for c in guild.channels if c.name.startswith("ticket-")) + 1
        chan = await guild.create_text_channel(f"ticket-{num}")
        await chan.set_permissions(interaction.user, read_messages=True, send_messages=True)
        admin_role = guild.get_role(ADMIN_ROLE)
        await chan.set_permissions(admin_role, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"Opened a ticket: {chan.mention}", ephemeral=True)
        await chan.send(f"{interaction.user.mention}, you have a new ticket!")

    button.callback = button_callback
    await ctx.send("Click the button to open a ticket:", view=view)

bot.run(TOKEN)
