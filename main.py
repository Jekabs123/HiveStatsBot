import discord
from discord.ext import commands
import topgg

def get_prefix(bot, message):
    """A callable Prefix for our bot. This could be edited to allow per server prefixes."""

    prefixes = ["hive ", "Hive "]

    return commands.when_mentioned_or(*prefixes)(bot, message)


client = commands.Bot(command_prefix=get_prefix)

client.remove_command("help")

extensions = [
    "cogs.stats",
    "cogs.error",
    "cogs.info",
    "cogs.help"
]

#extensions = []

for extension in extensions:
    try:
        client.load_extension(extension)
    except Exception as e:
        print(f"\nError while loading {extension}!\n{e}\n")


@client.event
async def on_ready():
    """http://discordpy.readthedocs.io/en/rewrite/api.html#discord.on_ready"""
    print(
        f'\n\nLogged in as: {client.user.name} - {client.user.id}\nVersion: {discord.__version__}\n')

    # Changes our bots Playing Status. type=1(streaming) for a standard game you could remove type and url.
    await client.change_presence(activity=discord.Game(name="hive help statistics"))
    
    if False: # Enable/Disable top.gg
        def topgg_post():
            dbl_token = ""  #! Set top.gg token
            client.topggpy = topgg.DBLClient(client, dbl_token, autopost=True, post_shard_count=True)
        
        print(f"Enabling top.gg auto post")
        topgg_post()

        @client.event
        async def on_autopost_success():
            print(
                f"Posted server count ({client.topggpy.guild_count}), shard count ({client.shard_count})"
            )
    else:
        print(f"Top.gg auto post disabled")

client.run("ODU4MjQwMTk4ODkwNjE4ODgx.YNbQeA.GVQMwXP36rZgac3Q5CV_qEs3DFs") #FIXME #! Set bot token

