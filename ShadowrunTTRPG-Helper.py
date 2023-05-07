import os
import discord
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("token")
client = discord.Client()

@client.event
async def on_ready():
# Print this when the bot starts up for the first time.
    print(f'{client.user} has connected to Discord!')
    
  # Set up faction information
REPUTATION_THRESHOLD = 10

# Data structure to store reputation information
reputation_data = {}

# Create a new bot instance with the prefix "!"
bot = commands.Bot(command_prefix="!")

def get_faction_status(reputation):
    if reputation >= 20:
        return "Friend"
    elif reputation >= 10:
        return "Colleague"
    elif reputation >= 0:
        return "Neutral"
    elif reputation >= -10:
        return "Enemy"
    else:
        return "Nemesis"

async def update_faction_messages(guild):
    channel = discord.utils.get(guild.channels, name="factions")
    if channel is not None:
        # Delete all messages in the factions channel
        async for message in channel.history(limit=100):
            await message.delete()

        # Create new messages for each faction with the current reputation values
        for faction in reputation_data:
            embed = discord.Embed(title=faction, description=f"Reputation: {reputation_data[faction]}", color=discord.Color.blue())
            message = await channel.send(embed=embed)
            await message.add_reaction("⬆️")
            await message.add_reaction("⬇️")

# Initialize the reputation_data dictionary
@bot.event
async def on_ready():
    for guild in bot.guilds:
        await update_faction_messages(guild)

# Update reputation values and faction messages when a reaction is added
@bot.event
async def on_raw_reaction_add(payload):
    channel = bot.get_channel(payload.channel_id)
    user = bot.get_user(payload.user_id)

    if channel.name == "factions" and user != bot.user:
        message = await channel.fetch_message(payload.message_id)
        embed = message.embeds[0]

        faction = embed.title
        if faction in reputation_data:
            if payload.emoji.name == "⬆️":
                reputation_data[faction] += 1
            elif payload.emoji.name == "⬇️":
                reputation_data[faction] -= 1

            # Update faction message
            await update_faction_messages(channel.guild)

            # Check if the reputation threshold is reached and send a message to the players channel
            if reputation_data[faction] >= REPUTATION_THRESHOLD:
                players_channel = discord.utils.get(channel.guild.channels, name="players")
                if players_channel is not None:
                    await players_channel.send(f"The reputation of {faction} has reached {REPUTATION_THRESHOLD}! Something important is happening!")

# Add a new faction
@bot.command(name="createfaction")
async def createfaction(ctx, *, faction_name: str):
    if faction_name not in reputation_data:
        reputation_data[faction_name] = 0
        await update_faction_messages(ctx.guild)
        await ctx.send(f"Faction {faction_name} created.")
    else:
        await ctx.send("This faction already exists.")

# Remove a faction
@bot.command(name="deletefaction")
async def deletefaction(ctx, *, faction_name: str):
    if faction_name in reputation_data:
        del reputation_data[faction_name]
        await update_faction_messages(ctx.guild)
        await ctx.send(f"Faction {faction_name} deleted.")
    else:
        await ctx.send("This faction does not exist.")

# Update a faction's reputation value
@bot.command(name="setreputation")
async def setreputation(ctx, faction_name: str, value: int):
       if faction_name in reputation_data:
        reputation_data[faction_name] = value
        await update_faction_messages(ctx.guild)
        await ctx.send(f"Reputation of {faction_name} set to {value}.")
    else:
        await ctx.send("This faction does not exist.")

# Get the status of all factions
@bot.command(name="factionstatus")
async def factionstatus(ctx):
    embed = discord.Embed(title="Faction Status", color=discord.Color.blue())

    for faction, reputation in reputation_data.items():
        status = get_faction_status(reputation)
        embed.add_field(name=f"{faction} ({reputation})", value=status, inline=False)

    await ctx.send(embed=embed)

# Run the bot
client.run(token)
