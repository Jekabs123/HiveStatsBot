import discord
from discord.ext import commands

class StartUp(commands.Cog):

    def __init__(self, client):
        self.client = client
        

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        EMSG = ""
        EDESC = ""
        if isinstance(error, commands.CommandNotFound):
            #print(f"{error}, server: {ctx.guild.name}, user: {ctx.author}")
            return

        elif isinstance(error, commands.TooManyArguments):
            EMSG = "To many arguments were given!"

        elif isinstance(error, commands.MissingRequiredArgument):
            EMSG = "Missing required arguments!"
            EDESC = f"Check .help [command] for the correct usage!"

        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            EMSG = "Extension already loaded!"
            EDESC = f"This extension is already loaded!"

        elif isinstance(error, commands.ExtensionNotFound):
            EMSG = "Extension not found!"
            EDESC = f"This extension was not found!"

        elif isinstance(error, commands.ExtensionNotLoaded):
            EMSG = "Extension has not been loaded!"
            EDESC = f"Extension has not been loaded!"

        elif isinstance(error, commands.ExtensionError):
            EMSG = "Extension error:"
            EDESC = f"{error}"

        elif isinstance(error, commands.MissingPermissions):
            error = str(error)
            error = error.replace("You are missing ","")
            error = error.replace(" permission(s) to run this command.","")

            EMSG = f"You are missing permission(s) {error} to run this commands."
            EDESC = f"You are missing the permission(s): `{error}` to use this command!`"

        elif isinstance(error, commands.UserInputError):
            EMSG = f"Input error: {error}"
            EDESC = f"{error}"

        elif isinstance(error, commands.BotMissingPermissions):
            EMSG = f"I am missing permission(s) {error}"
            EDESC = f"{error}"

        elif isinstance(error, commands.PrivateMessageOnly):
            EMSG = f"This command only works in DMs/PMs!"

        elif isinstance(error, commands.NoPrivateMessage):
            EMSG = f"This command only works in servers!"
        
        elif isinstance(error, commands.CommandOnCooldown):
            time = str(error).replace("You are on cooldown. Try again in ", "")
            EMSG = "You are on a cooldown"
            EDESC = f"Try again in {time}"

        else:
            EMSG = f"Something went wrong and I'm not quite sure what."

        embed = discord.Embed(title = EMSG,description=EDESC, color=0xff0000)
        
        try:
            await ctx.reply(embed=embed)
        except Exception:
            try:
                await ctx.reply(f"Something went wrong.")
            except Exception:
                pass
        


        print(f"Error handler: {error}", exc_info=True)
            

def setup(client):
    client.add_cog(StartUp(client))
