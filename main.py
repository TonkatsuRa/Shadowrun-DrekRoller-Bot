import os
import discord
import yaml
import random
from discord.ext import commands, menus #pip install discord-ext-menus
from typing import Optional, Literal
from discord.ext import commands
from discord.ext.commands import Context
from discord.ext.commands import Greedy
from discord.ext.commands import Bot
from discord import app_commands

TOKEN = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" #YOUR BOT TOKEN

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents, help_command=None) 

#===================================================
#                 HELP MENU
#==================================================
# https://fiu-original.b-cdn.net/fontsinuse.com/use-images/167/167331/167331.png Shadowrun Logo


@bot.tree.command(name='help', description="Help command for this bot")
async def help(interaction):
    await interaction.response.defer()  # Defer the initial response

    groups = [city, media, sense, npc, matrix, runner]  # replace with your actual groups
    descriptions = {
        city: "Random tables about City, streets and buildings",
        media: "Random tables about TV, music and media",
        sense: "Random tables about sensory impressions for players",
        npc: "Random tables to generate different kind of NPC's",
        matrix: "Random table to generate matrix, data devices etc.",
        runner: "Random tables to generate missions and misc. things for Shadowrunners",
    }
    embeds = []

    # Create the landing page
    landing_page = discord.Embed(title="Shadowrun DrekRoller Helpdesk", description="Here are the available command groups:", color=discord.Color.blue())
    for i, group in enumerate(groups, start=1):
        landing_page.add_field(name=f"(Page {i+1}) - {group.name} : {descriptions[group]}", value="\u200b", inline=False)
    embeds.append(landing_page)

    # Create the other pages
    for i, group in enumerate(groups, start=1):
        embed = discord.Embed(title=f"Page {i+1}", description=f"Help page for {group.name}", color=discord.Color.blue())
        for command in group.commands:
            embed.add_field(name=command.name, value=command.help, inline=False)
        embeds.append(embed)

    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣']

    message = await interaction.channel.send(embed=embeds[0])  # send the first page
    for reaction in reactions[:len(embeds)]:
        await message.add_reaction(reaction)  # add the reactions

    def check(reaction, user):
        return user == interaction.user and str(reaction.emoji) in reactions

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=120.0, check=check)
            await message.edit(embed=embeds[reactions.index(str(reaction))])
            await message.remove_reaction(reaction, user)
        except:
            break

    await message.clear_reactions()

#=========================================
#              ON READY
#=========================================


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    print("Registered commands:")
    for command in bot.commands:
        print(command.name)
    for command in city.commands:
        print(command.name)
    for command in media.commands:
        print(command.name)
    for command in sense.commands:
        print(command.name)
    for command in npc.commands:
        print(command.name)   
    for command in matrix.commands:
        print(command.name)
    for command in runner.commands:
        print(command.name)     
    await bot.wait_until_ready()


#============================================
#                   Sync commands
#============================================

# Authorized user ID
AUTHORIZED_USER_ID = 420302340193517568

@bot.command()
async def sync(
  ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:

    if ctx.author.id != AUTHORIZED_USER_ID:
        await ctx.send("Sorry, this command is restricted to the authorized user.")
        return
      
    print("sync command called")  # Debugging output
    try:
        if not guilds:
            if spec == "~":
                print("Syncing to current guild...")  # Debugging output
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                print("Copying global commands to current guild...")  # Debugging output
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                print("Clearing commands from current guild...")  # Debugging output
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                print("Syncing globally...")  # Debugging output
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            print(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")  # Debugging output
            return

        ret = 0
        for guild in guilds:
            try:
                print(f"Syncing to guild {guild.id}...")  # Debugging output
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                print(f"Failed to sync to guild {guild.id}")  # Debugging output
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")
        print(f"Synced the tree to {ret}/{len(guilds)}.")  # Debugging output
    except Exception as e:
        # Send a message with the error details
        await ctx.send(f"An error occurred: {type(e).__name__} - {e}")
        print(f"An error occurred: {type(e).__name__} - {e}")  # Debugging output


#commands.Greedy`
#discord.Object`
#typing.Optional` and `typing.Literal`

#Works like:
#!sync` -> global sync
#!sync ~` -> sync current guild
#!sync *` -> copies all global app commands to current guild and syncs
#!sync ^` -> clears all commands from the current guild target and syncs (removes guild commands)
#!sync id_1 id_2` -> syncs guilds with id 1 and 2

#=========================================
#              ERROR HANDLING
#=========================================

# it is used for the cooldown to prevent the bot from spam attack
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"**Try after {round(error.retry_after, 2)} seconds.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'This command is on cooldown, please retry in {math.ceil(error.retry_after)}s.')
    elif isinstance(error, commands.CommandInvokeError):
        original = error.original
        if isinstance(original, discord.HTTPException) and original.status == 429:
            await ctx.send('I am being rate limited by Discord, please wait a moment before trying again.')
    else:
        # handle other types of errors
        pass
#====================================================
#                SETUP
#====================================================

# This is your roll logic function
async def roll_logic(ctx, tables, message_format, num_rolls=1):
    # Defer response
    await ctx.defer()

    with open("RandomRolls.yaml", 'r') as stream:
        try:
            roll_tables = yaml.safe_load(stream)
            if roll_tables:
                results = []
                for table in tables:
                    table_results = []
                    for _ in range(num_rolls):
                        result = random.choice(list(roll_tables[table].values()))
                        table_results.append(result)
                    results.append(" and ".join(table_results))

                message = message_format.format(*results)
                # Send the actual response
                await ctx.send(message)
        except yaml.YAMLError as exc:
            print(exc)


@bot.hybrid_group(name='city', help="Commands about urban life, buildings, streets and cars.")
async def city(ctx):
    await ctx.send('Invalid sub command passed...')

@bot.hybrid_group(name='media', help="Commands about generating TV, Music, AR and Ads related content.")
async def media(ctx):
    await ctx.send('Invalid sub command passed...')

@bot.hybrid_group(name='npc', help="Commands about generating NPC's.")
async def npc(ctx):
    await ctx.send('Invalid sub command passed...')

@bot.hybrid_group(name='matrix', help="Commands about generating Matrix and Data related content.")
async def matrix(ctx):
    await ctx.send('Invalid sub command passed...')

@bot.hybrid_group(name='sense', help="Commands about generating sensory experiences like smell, sight, sounds etc.")
async def sense(ctx):
    await ctx.send('Invalid sub command passed...')

@bot.hybrid_group(name='runner', help="Commands about generating missions, runner life things and other content.")
async def runner(ctx):
    await ctx.send('Invalid sub command passed...')

# ==================================================================
#                        Roll Commands
# ==================================================================

@city.command(name='buildings', help="Description of a random building")
async def buildings(ctx):
    tables = [
        "1_Building_Type",
        "1_Building_Feature",
        "1_Quirky_Style",
        "1_Quirky_State",
        "1_Quirky_Feature",
        "1_Quirky_Secret",
    ]
    message_format = "You see a {} that is {} with a {} style and {} look. There are {} and a secret {}."
    await roll_logic(ctx, tables, message_format)


@sense.command(name='smell', help="Desribing a random smell. Add a number after the command to generate multiple smells")
async def smell(ctx, num_rolls: int = 1):
    tables = ["8_Smell"]
    message_format = "You smell {}."
    await roll_logic(ctx, tables, message_format, num_rolls)


@npc.command(name='conflictgroup', help="Generate a random group and what kind of conflict they have with another group")
async def conflictgroup(ctx):
    tables = [
        "2_Conflict_Group",
        "2_Conflict_Source",
        "2_Conflict_Opposing",
    ]
    message_format = "The group {} are/is in conflict because {} with/against {}."
    await roll_logic(ctx, tables, message_format)


@city.command(name='business', help="Generate a random small street business")
async def business(ctx):
    tables = [
        "3_AltBusiness_Quality",
        "3_AltBusiness_Status",
        "3_AltBusiness_Type",
        "3_AltBusiness_Security",
    ]
    message_format = "A {} and {} {}. There is/are {} for security on the premises."
    await roll_logic(ctx, tables, message_format)


@city.command(name='streetfinds', help="Generates a random odd or weird 'thing' you can find on the streets")
async def streetfinds(ctx):
    tables = ["4_Weird_Street_Finds"]
    message_format = "You stumble upon a {}."
    await roll_logic(ctx, tables, message_format)


@city.command(name='legacyinfrastructure', help="Rolls a random legacy building or part of old infrastructure")
async def legacyinfrastructure(ctx):
    tables = ["5_Legacy_Infrastructure"]
    message_format = "You stumble upon a {}."
    await roll_logic(ctx, tables, message_format)


@matrix.command(name='legacydata', help="Rolls a random type of legacy Data device or paydata")
async def legacydata(ctx):
    tables = ["6_Legacy_Data"]
    message_format = "You stumble upon a {}."
    await roll_logic(ctx, tables, message_format)


@city.command(name='nightlife', help="Rolls a random nightlife location")
async def nightlife(ctx):
    tables = [
        "7_Nightlife_Location",
        "7_Nightlife_Status",
        "7_Nightlife_Security",
        "7_Nightlife_Vibe",
    ]
    message_format = "The nightclub '{}' has/is {}. The on-site security is/are {}. The vibe of the place is {}."
    await roll_logic(ctx, tables, message_format)

@media.command(name='music', help="Rolls a random futuristic music genre")
async def music(ctx):
    tables = ["25_Music_Genre"]
    message_format = "You would describe the music genre as {}"
    await roll_logic(ctx, tables, message_format)

@sense.command(name='sound', help="Describing a random sound. Add a number after the command to roll multiple sounds")
async def sound(ctx, num_rolls: int = 1):
    tables = ["8_Sounds"]
    message_format = "You hear {}"
    await roll_logic(ctx, tables, message_format, num_rolls)

@sense.command(name='gutfeeling', help="Describing a random gutfeeling. Add a number after the command to roll multiple gutfeelings")
async def gutfeeling(ctx, num_rolls: int = 1):
    tables = ["8_Gut_Feeling"]
    message_format = "You can't shake the feeling that {}"
    await roll_logic(ctx, tables, message_format, num_rolls)

@sense.command(name='sight', help="Describing a random sight. Add a number after the command to roll multiple sights")
async def sight(ctx, num_rolls: int = 1):
    tables = ["8_Sights"]
    message_format = "You see {}"
    await roll_logic(ctx, tables, message_format, num_rolls)

@media.command(name='ad', help="Roll a random advertisement")
async def ad(ctx):
    tables = [
        "9_Infotainment_Marketing_Style",
        "9_Infotainment_Brand",
        "9_Infotainment_Range",
        "9_Infotainment_Product_Line",
    ]
    message_format = "You see a {} commercial for {} {} {} product."
    await roll_logic(ctx, tables, message_format)

@city.command(name='cars', help="Roll a random car on the street")
async def cars(ctx, num_rolls: int = 1):
    tables = ["10_Road_Vehicles"]
    message_format = "You see {}"
    await roll_logic(ctx, tables, message_format, num_rolls)

@media.command(name='ar', help="Roll a random augmented reality AR-Icon")
async def ar(ctx):
    tables = [
        "11_AR_Type",
        "11_AR_Aesthetic",
        "11_AR_Image_Style",
    ]
    message_format = "The AR image is about {} with {} and {}."
    await roll_logic(ctx, tables, message_format)

@npc.command(name='citizen', help="Rolls a random citizen")
async def citizen(ctx):
    tables = [
        "12_Instacitizen",
        "12_Instacitizen_Impression",
        "12_Instacitizen_Looks",
        "12_Instacitizen_Style",
        "12_Instacitizen_Vibe",
        "12_Instacitizen_Accessories",
    ]
    message_format = "He/She is a {}. Your first impression is {} with {}. He/She has {} and their vibe is {}. What's special about them is, that they are/have {}"
    await roll_logic(ctx, tables, message_format)

@npc.command(name='needs', help="Rolls a random nefarious need of an NPC and how badly they need to have it")
async def needs(ctx):
    tables = [
        "13_Wants",
        "13_Level_Of_Need",
    ]
    message_format = "**Wants**: {}. **Level of need**: {}"
    await roll_logic(ctx, tables, message_format)

@npc.command(name='tattoo', help="Roll a random tattoo")
async def tattoo(ctx):
    tables = [
        "14_Tattoo_Style",
        "14_Tattoo_What",
        "14_Tattoo_Where"
    ]
    message_format = "The tattoo {} {}. It is tattooed {}."
    await roll_logic(ctx, tables, message_format)

@npc.command(name='streetwalker', help="Roll a random streetwalker")
async def streetwalker(ctx):
    tables = [
        "15_Streetwalker_Genderidentity",
        "15_Streetwalker_Type",
    ]
    message_format = "You see a {} streetwalker, {}"
    await roll_logic(ctx, tables, message_format)

@npc.command(name='salaryman', help="Roll a random corporate salaryman")
async def salaryman(ctx):
    tables = [
        "16_Corpo_Name",
        "16_Corpo_Surname",
        "16_Corpo_Job",
        "16_Corpo_Quirk",
        "16_Corpo_Look",
    ]
    message_format = "They introduce themselves as {} {}. They work as {} and their quirk is {}. They can be described as {}"
    await roll_logic(ctx, tables, message_format)

@runner.command(name='corpomission', help="Roll a random corporate mission")
async def corpomission(ctx):
    tables = [
        "17_Corpo_Mission",
        "17_Corpo_Ressources",
        "17_Corpo_Twist",
    ]
    message_format = "**Job**: \n- {}. \n- {}. \n- {}"
    await roll_logic(ctx, tables, message_format)

@runner.command(name='randomevent', help="Roll a random event that can happy any time and anywhere")
async def randomevent(ctx, num_rolls: int = 1):
    tables = ["17_Random_Event"]
    message_format = "**Random Event**: {}"
    await roll_logic(ctx, tables, message_format, num_rolls)

@runner.command(name='trap', help="Rolls a random trap. Add numbers after the command to roll multiple traps")
async def trap(ctx, num_rolls: int = 1):
    tables = ["17_BoobyTrap"]
    message_format = "**Booby Trap**: {}"
    await roll_logic(ctx, tables, message_format, num_rolls)

@npc.command(name='gang', help="Roll a random gang")
async def gang(ctx):
    tables = [
        "18_Gang_Name1",
        "18_Gang_Name2",
        "18_Gang_Name3",
        "18_Gang_Name4",
        "18_Gang_Activity",
        "18_Gang_Deal",
        "18_Gang_Rumor"
    ]
    message_format = "**They are known as {} {} {} {}**. \nTheir business is: {}, and their deal is: {}. It is rumored that: {}."
    await roll_logic(ctx, tables, message_format)

@npc.command(name='police', help="Roll a random law enforcement unit description")
async def police(ctx):
    tables = [
        "19_Police_Department",        
        "19_Police_Type",
        "19_Police_Jobs",
        "19_Police_Response_Level",
    ]
    message_format = "{} has sent {}. They are {}. {}."
    await roll_logic(ctx, tables, message_format)

@npc.command(name='policebackup', help="Roll random law enforcement backup unit description")
async def policebackup(ctx):
    tables = [
        "19_Police_Backup",        
        "19_Police_Tactics",
    ]
    message_format = "The law enforcers on site have requested backup. The HQ sends {} and they're going to use {}"
    await roll_logic(ctx, tables, message_format)

@npc.command(name='fixer', help="Roll a random fixer contact")
async def fixer(ctx):
    tables = [
        "20_Fixer_Type",        
        "20_Fixer_Job",
        "20_Fixer_Circumstances",
        "20_Fixer_Job",
        "20_Fixer_Look"
    ]
    message_format = "Your Fixers name is {} and their job is being a {}. They/They're {} {}. Your first impression of them is: {}"
    await roll_logic(ctx, tables, message_format)

@npc.command(name='hiredgun', help="Roll a random hired gun")
async def hiredgun(ctx):
    tables = [
        "24_Hired_Gun",        
        "24_Hired_Gun_Weapon",
        "24_Hired_Gun_Clothing",
        "24_Hired_Gun_Circumstance",
        "21_Client_Type"
    ]
    message_format = "The hired gun introduces themselves as {}. They're wielding as a weapon a {}. Your first impression of them is: {}. And in the past: {} {}."
    await roll_logic(ctx, tables, message_format)

@runner.command(name='mrjohnsonjob', help="Roll a random job from a Mr.Johnson")
async def mrjohnsonjob(ctx):
    tables = [
        "21_MrJohnson_Type",        
        "21_MrJohnson_Want",
        "21_MrJohnson_Target",
        "21_MrJohnson_Action",
        "17_Corpo_Twist",
    ]
    message_format = "The Johnsons introduces himself as a {}. He/She {} a {}. To achieve this goal he needs the players to {} someone. {}"
    await roll_logic(ctx, tables, message_format)

@matrix.command(name='datadevice', help="Roll a random Data Device")
async def datadevice(ctx):
    tables = [
        "22_DataDevice_Content",        
        "22_DataDevice_History",
    ]
    message_format = "On the Data Device you find {}. Given the data on it, it seems to be {}"
    await roll_logic(ctx, tables, message_format)

@matrix.command(name='sota', help="Roll a random State-of-the-Art Device")
async def sota(ctx):
    tables = [
        "22_StateOfTheArt_Type",        
        "22_StateOfTheArt_Condition",
    ]
    message_format = "You find a {}. Its condition/specifications is {}."
    await roll_logic(ctx, tables, message_format)

@runner.command(name='clutter', help="Roll a random useless items. Add a number after the command to roll multiple clutter items")
async def clutter(ctx, num_rolls: int = 1):
    tables = ["23_Corpse_Object"]
    message_format = "You find: {}"
    await roll_logic(ctx, tables, message_format, num_rolls)

@runner.command(name='corpse', help="Roll a random description for a corpse")
async def corpse(ctx):
    tables = [
        "23_Corpse_Description",        
    ]
    message_format = "You look at the corpse in front of you. You find:  '*{}*'"
    await roll_logic(ctx, tables, message_format)

@npc.command(name='client', help="Roll a random type of client")
async def client(ctx):
    tables = [
        "21_Client_Type",        
        "21_Client_Want",
        "21_Client_Action",
        "21_Client_Item",
    ]
    message_format = "The client is a {} and and they {} {} a {}."
    await roll_logic(ctx, tables, message_format)

@media.command(name='socialmedia', help="Roll random social media content. Add a number to roll multiple social media contents")
async def socialmedia(ctx, num_rolls: int = 1):
    tables = ["25_Social_Media"]
    message_format = "You check out the social media on the matrix. You summarise the content as: {}."
    await roll_logic(ctx, tables, message_format, num_rolls)

@media.command(name='tv', help="Roll a random TV-Show. Add a number after the command to roll multiple shows")
async def tv(ctx, num_rolls: int = 1):
    tables = ["25_TV_Shows"]
    message_format = "You stare at the screen, watching a TV-show. The show is called {}."
    await roll_logic(ctx, tables, message_format, num_rolls)

@city.command(name='atypicalweather', help="Roll a random type of dangerous or atypical weather to annoy your players")
async def atypicalweather(ctx):
    tables = [
        "25_Atypical_Weather",        
    ]
    message_format = "You check your surroundings. The Weather is unusual today. You would describe it as: {}."
    await roll_logic(ctx, tables, message_format)

@runner.command(name='insult', help="Throw random insults at your players. Add a number after the command to insult them multiple times")
async def insult(ctx, num_rolls: int = 1):
    tables = ["26_Insults"]
    message_format = "You seem to have offended the Person in front of you. They tell you: '*{}*'"
    await roll_logic(ctx, tables, message_format, num_rolls)

@city.command(name='street', help="Roll a random street with detailed description")
async def street(ctx):
    tables = [
        "27_Street_Description",        
        "27_Street_Condition",
        "27_Augmented_Reality_Ads",
        "27_Building_Sights",
    ]
    message_format = "You see {} {} {} {}"
    await roll_logic(ctx, tables, message_format)

@city.command(name='publictransport', help="Roll a random public transport vehicle description")
async def publictransport(ctx):
    tables = [
        "27_Public_Transport_Vehicles",        
        "27_Public_Transport_Condition",
        "27_Public_Transport_Passengers",
        "27_Public_Transport_Passengers",
        "27_Public_Transport_Passengers",
        "27_Public_Transport_Sensory",
        "27_Public_Transport_Driver",
    ]
    message_format = "Your public transport vehicle is a {}. {} Among the passengers you see {} {} {}.{} It is driven by {}"
    await roll_logic(ctx, tables, message_format)

@runner.command(name='publicencounter', help="Roll a random public encounter on the street")
async def publicencounter(ctx):
    tables = [
        "27_Public_Encounter",        
        "27_Public_Encounter_Scam",
    ]
    message_format = "{} {}"
    await roll_logic(ctx, tables, message_format)
  
#===========================================  
#               END
# ==========================================  
# Token
bot.run(TOKEN)


