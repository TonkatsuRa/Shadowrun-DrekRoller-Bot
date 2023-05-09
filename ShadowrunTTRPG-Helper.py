import os
import discord
import json
from discord.ext import commands
from dotenv import load_dotenv

# Read the token from the environment variable
token = os.environ['TOKEN']

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

# Create a new bot instance with the prefix "!"
bot = commands.Bot(command_prefix="!", intents=intents)

# Remove the default help command
bot.remove_command("help")

# Functions to save and load data
def save_data():
    data = {
        "reputation_data": reputation_data,
        "gm_channel_name": gm_channel_name
    }

    with open("data.json", "w") as outfile:
        json.dump(data, outfile)


def load_data():
    global reputation_data, gm_channel_name
    if not os.path.isfile('data.json'):
        with open('data.json', 'w') as outfile:
            json.dump({"reputation_data": {}, "gm_channel_name": "gm"}, outfile)
    with open('data.json', 'r') as infile:
        data = json.load(infile)
        reputation_data = data['reputation_data']
        gm_channel_name = data['gm_channel_name']


# Data structure to store reputation information
REPUTATION_THRESHOLD = 10
reputation_data = {}
gm_channel_name = "gm"

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

# Bot Reputation commands
async def show_factions_embed(ctx, in_gm_channel=False):
    embed = discord.Embed(title="Factions", color=discord.Color.blue())
    for faction, reputation in reputation_data.items():
        status = get_faction_status(reputation)
        embed.add_field(name=f"{faction} ({reputation})", value=status, inline=False)

    message = await ctx.send(embed=embed)

    if in_gm_channel:
        await message.add_reaction("⬆️")
        await message.add_reaction("⬇️")

async def update_faction_messages(guild):
    gm_channel = discord.utils.get(guild.channels, name=gm_channel_name)
    if gm_channel is not None:
        async for message in gm_channel.history():
            if message.author == bot.user and len(message.embeds) > 0:
                await message.delete()
        await show_factions_embed(gm_channel, in_gm_channel=True)

# load JSON and stored Data
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    load_data()
    for guild in bot.guilds:
        await update_faction_messages(guild)

# Custom help command
@bot.command(name="help")
async def custom_help(ctx):
    embed = discord.Embed(title="Help", description="List of available commands:", color=discord.Color.blue())

    embed.add_field(name="!faction add <faction_name>", value="Create a new faction with the given name.", inline=False)
    embed.add_field(name="!faction delete <faction_name>", value="Delete a faction with the specified name.", inline=False)
    embed.add_field(name="!faction list", value="List all created factions and their reputation levels.", inline=False)
    embed.add_field(name="!rep set <channel_name>", value="Sets the name of the channel where the GM texts will be posted.", inline=False)
    embed.add_field(name="!rep show", value="Posts all factions as messages in an embed and adds arrow up and arrow down buttons to increase or decrease the reputation.", inline=False)

    await ctx.send(embed=embed)


@bot.command(name="rep")
async def rep(ctx, action: str, channel_name: str = ""):
    if action.lower() == "set":
        if channel_name:
            global gm_channel_name
            gm_channel_name = channel_name
            save_data()
            await ctx.send(f"The GM channel name has been set to {channel_name}.")
        else:
            await ctx.send("The channel name is missing.")
    elif action.lower() == "show":
        gm_channel = discord.utils.get(ctx.guild.channels, name=gm_channel_name)
        if gm_channel is not None:
            await show_factions_embed(gm_channel, in_gm_channel=True)
            await ctx.send("Faction messages have been updated in the GM channel.")
        else:
            await ctx.send("GM channel not found. Please set the GM channel first.")
    else:
        await ctx.send("Invalid action. Use 'set' or 'show'.")

@bot.command(name="faction")
async def faction(ctx, action: str, *, faction_name=None):
    if action.lower() == "add":
        if faction_name and faction_name not in reputation_data:
            reputation_data[faction_name] = 0
            save_data()
            await ctx.send(f"Faction {faction_name} added.")
        else:
            await ctx.send("This faction already exists or the faction name is missing.")
    elif action.lower() == "delete":
        if faction_name and faction_name in reputation_data:
            del reputation_data[faction_name]
            save_data()
            await ctx.send(f"Faction {faction_name} deleted.")
        else:
            await ctx.send("This faction does not exist or the faction name is missing.")
    elif action.lower() == "list":
        await show_factions_embed(ctx)
    else:
        await ctx.send("Invalid action. Use 'add', 'delete', or 'list'.")

@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.channel.name == gm_channel_name and user != bot.user:
        embed = reaction.message.embeds[0]
        faction = embed.title

        if faction in reputation_data:
            if reaction.emoji == "⬆️":
                reputation_data[faction] += 1
            elif reaction.emoji == "⬇️":
                reputation_data[faction] -= 1

            save_data()
            await update_faction_messages(reaction.message.guild)

@bot.event
async def on_reaction_remove(reaction, user):
    if reaction.message.channel.name == gm_channel_name and user != bot.user:
        embed = reaction.message.embeds[0]
        faction = embed.title

        if faction in reputation_data:
            if reaction.emoji == "⬆️":
                reputation_data[faction] -= 1
            elif reaction.emoji == "⬇️":
                reputation_data[faction] += 1

            save_data()
            await update_faction_messages(reaction.message.guild)

# Run the bot
bot.run(token)

