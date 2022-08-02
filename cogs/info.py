import discord
from discord.ext import commands

def simple_embed(title, description, color = 0x003469):
    embed = discord.Embed(title = title, description = description, color = color)
    embed.set_footer(text = 'Made by AUser0#3289. If you find any bugs please DM me.')
    return embed

class info(commands.Cog, name="other"):

    def __init__(self, client):
        self.client = client

    @commands.command(name="invite")
    async def inviteCommand(self, ctx):
        """Add me to your server"""
        embed=discord.Embed(title="Click here to add me to your server", url="https://discord.com/api/oauth2/authorize?client_id=856872237143162900&permissions=2147798080&scope=bot")
        await ctx.reply(embed=embed)
            

def setup(client):
    client.add_cog(info(client))
