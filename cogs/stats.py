import discord
from discord.ext import commands
import aiohttp
import json
from datetime import datetime, timedelta, timezone
from PIL import ImageFont, Image, ImageDraw
from io import BytesIO
import asyncio
import sqlite3

def simple_embed(title, description, color=0x003469):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(
        text='Made by AProx#3289. If you find any bugs please DM me.')
    return embed


class statsCog(commands.Cog, name="statistics"):
    def __init__(self, bot):
        self.error_embed = simple_embed('Looks like you did something wrong', f'Do `hive help statistics` to see how to use this command.', 0xB50000)
        print(f"{self.qualified_name} loaded")

        self.client = bot

        self.apiBaseURI = 'https://api.playhive.com/v0'

        self.con = sqlite3.connect(f"./files/database/main.db")
        self.cur = self.con.cursor()

        self.cache = {}

        self.games = {
            'wars': ['wars', 'tw', 'treasurewars'],
            'dr': ["dr", "deathrun", "run"],
            "hide": ["hide", "seek", "hidenseek", "hideandseek", "hns"],
            "sg": ["sg", "survival", "survivalgames"],
            "murder": ["murder", "mystery", "murdermystery", "mm"],
            "sky": ["sky", "skyways", "sky-wars", "sw"]
        }
        self.gameFullName = {
            "wars": "Treasure Wars",
            "dr": "Deathrun",
            "hide": "Hide and Seek",
            "sg": "Survival games",
            "murder": "Murder Mystery",
            "sky": "Skywars"
        }

        self.imageTextColor = (173, 183, 184)
        self.imageValueColor = (255, 255, 255)
        self.imageBackgroundColor = (46, 64, 84)
        self.imageTextLeftMargin = 10
        self.imageFirstLineTopMargin = 10
        self.imageValueLeftMargin = 400
        self.fontSize = 38

        self.imageFont = ImageFont.truetype('./arial.ttf', self.fontSize)

        self.specialPeople = ["AUser0"]

        self.roundDataTo = 4

        self.lbcache = {}

    def cog_unload(self):
        print("Closing database.")
        self.con.close()

    async def get_data(self, endpoint):
        async with aiohttp.ClientSession() as session:

            url = self.apiBaseURI + endpoint
            async with session.get(url) as resp:
                return resp.status, await resp.text()

    def checkIfSpecial(self, text):
        if len(text) > 16 or len(text) < 3:
            return False

        self.cur.execute(
            'SELECT * FROM users WHERE (minecraft_name=?)', (str(text.lower()),))
        entries = self.cur.fetchall()

        for entry in entries:
            if entry[2] != 0:
                return True

        return False

    def createImage(self, data):
        "Draw a text on an Image, saves it, show it"

        # Define all properties

        listNames = list(data["items"].keys())
        listValues = list(data["items"].values())

        imageHeight = int(((((len(listNames) + 1) * self.fontSize)) +
                          self.fontSize / 2) + self.imageFirstLineTopMargin * 2 + self.fontSize)
        imageSize = (640, imageHeight)

        if "special" in data and data["special"]:
            usernameWidth = len(data["topText"]) * self.fontSize
            gradient = Image.open(
                './files/images/horizontal_gradient.png').resize((usernameWidth, imageHeight))

            # Create new alpha channel - solid black
            alpha = Image.new('L', (usernameWidth, imageHeight))
            draw = ImageDraw.Draw(alpha)

            draw.text((10, 10), data["topText"],
                      fill='white', font=self.imageFont)

            # Use text cutout as alpha channel for gradient image
            gradient.putalpha(alpha)

            image = Image.new('RGB', imageSize, self.imageBackgroundColor)
            image.paste(gradient, gradient)

            draw = ImageDraw.Draw(image)
        else:
            # create image
            image = Image.new(mode="RGB", size=imageSize,
                              color=self.imageBackgroundColor)
            draw = ImageDraw.Draw(image)

            # draw first line (name)
            draw.text((self.imageTextLeftMargin, self.imageFirstLineTopMargin),
                      data["topText"], font=self.imageFont, fill=self.imageValueColor)

        # Draw line between first line (name) and other text

        draw.line((0, self.imageFirstLineTopMargin + self.fontSize + (self.fontSize / 4),
                  imageSize[0], self.imageFirstLineTopMargin + self.fontSize + (self.fontSize / 4)), fill=self.imageTextColor, width=2)

        for n in range(len(listValues)):
            listValues[n] = str(listValues[n])

        if "valueLeftMargin" in data:
            imageValueLeftMargin = data["valueLeftMargin"]
        else:
            imageValueLeftMargin = self.imageValueLeftMargin

        for i in range(len(listNames)):
            cheight = ((((i + 1) * self.fontSize)) + self.fontSize / 2) + \
                self.imageFirstLineTopMargin  # Calculate height for current line

            # Draw name and value
            draw.text((self.imageTextLeftMargin, cheight),
                      listNames[i], font=self.imageFont, fill=self.imageTextColor)
            draw.text((imageValueLeftMargin, cheight),
                      listValues[i], font=self.imageFont, fill=self.imageValueColor)

        draw.text((self.imageTextLeftMargin, imageHeight - self.fontSize - self.fontSize / 2 + self.imageFirstLineTopMargin),
                  "Created with The Hive Statistics bot", font=self.imageFont, fill=(252, 240, 151))

        return image

    @commands.command(name='stats', aliases=['statistics', 's'])
    async def statsCommand(self, ctx, game=None, *, username=None):
        """Displays a players all time statistics.

        Usage: `hive [statistics|s] {game} {username}`

        Games:
         Treasure Wars  - tw
         Skywars        - sw
         Hide and Seek  - hns
         Deathrun       - dr
         Survival Games - sg
         Murder Mystery - mm
        """
        # Check for missing input
        await ctx.trigger_typing()

        if game is None or username is None:
            await ctx.reply(embed=self.error_embed)
            return

        gameID = None
        # Check for aliases
        for gameIDCheck, aliases in self.games.items():
            if game in aliases:
                gameID = gameIDCheck
                break

        # Check if game not found
        if gameID is None:
            await ctx.reply(embed=self.error_embed)
            return

        now = datetime.now(timezone.utc)
        if username in self.cache and gameID in self.cache[username] and now - self.cache[username][gameID]["time"] < timedelta(minutes=10):
            responseCode = self.cache[username][gameID]["responseCode"]
            responseText = self.cache[username][gameID]["responseText"]
            time = self.cache[username][gameID]["time"]

            if "[]" in responseText or responseText == []:
                await ctx.reply(embed=simple_embed("Could not get data", f"{username} has not played {self.gameFullName[gameID]}"))
                return

        else:
            try:
                responseCode, responseText = await self.get_data(f'/game/all/{gameID}/{username}')

                if not username in self.cache:
                    self.cache[username] = {}

                if responseCode in [200, 404]:

                    self.cache[username][gameID] = {
                        "responseCode": responseCode,
                        "responseText": responseText,
                        "time": now
                    }
                time = now

                if "[]" in responseText or responseText == []:
                    await ctx.reply(embed=simple_embed("Could not get data", f"`{username}` has not played {self.gameFullName[gameID]}"))
                    return

            except Exception as e:
                print(
                    f"Info: Not cache, {responseCode} {responseText}", exc_info=True)
                return

        try:
            if responseCode == 200:
                data = json.loads(responseText)

                dataDisplay = await self.createText(username, data, gameID)

                loop = asyncio.get_running_loop()

                image = await loop.run_in_executor(  # Create image in another thread to prevent blocking
                    None, self.createImage, (dataDisplay)
                )

                with BytesIO() as image_binary:
                    image.save(image_binary, 'PNG')
                    image_binary.seek(0)

                    embed = discord.Embed(
                        title=f"{username}'s {self.gameFullName[gameID]} stats")

                    file = discord.File(fp=image_binary, filename='stats.png')
                    embed.set_image(url="attachment://stats.png")

                    embed.set_footer(text=f"Requested by {ctx.author}")
                    embed.timestamp = time

                    await ctx.reply(embed=embed, file=file)

            elif responseCode == 404:
                await ctx.reply(embed=simple_embed('Unknown user!', f'User with that name not found, check your spelling and try again.', 0xB50000))
                return
            else:
                await ctx.reply(embed=simple_embed('Unknown error.', f'There was a problem with getting statistics, try again later.', 0xB50000))
                return

        except Exception as e:
            print("", exc_info=True)

    @commands.command(name='leaderboard', aliases=['lb'])
    async def leaderboardCommand(self, ctx, game=None, gtype="monthly", amount=None):
        """Displays the current monthly or all time leaderboards.

        Usage: `hive [leaderboard|lb] [game] {leaderboard type} {amount of players}`

        Games:
         Treasure Wars  - tw
         Skywars        - sw
         Deathrun       - dr
         Survival Games - sg
         Murder Mystery - mm

        Leaderboards:
         Monthly
         All
        """
        # Check for missing input
        if game is None:
            await ctx.reply(embed=self.error_embed)
            return
        if gtype not in ["monthly", "all"]:
            gtype = "monthly"

        if amount is None:
            amount = 10

        if type(amount) != int:
            amount = 10

        if amount < 5:
            amount = 5

        await ctx.trigger_typing()

        now = datetime.now(timezone.utc)

        gameID = None
        # Check for aliases
        for gameIDCheck, aliases in self.games.items():
            if game in aliases:
                gameID = gameIDCheck
                break

        if gameID in self.lbcache and gtype in self.lbcache[gameID] and now - self.lbcache[gameID][gtype]["time"] < timedelta(minutes=60):
            responseCode = self.lbcache[gameID][gtype]["responseCode"]
            responseText = self.lbcache[gameID][gtype]["responseText"]
            time = self.lbcache[gameID][gtype]["time"]
        else:
            try:
                responseCode, responseText = await self.get_data(f'/game/{gtype}/{gameID}')

                if not gameID in self.cache:
                    self.lbcache[gameID] = {}

                if responseCode in [200, 404]:
                    self.lbcache[gameID][gtype] = {
                        "responseCode": responseCode,
                        "responseText": responseText,
                        "time": now
                    }
                time = now
            except Exception as e:
                print(
                    f"Info: Not cache, {responseCode} {responseText}", exc_info=True)
                return

        try:
            if responseCode == 200:
                data = json.loads(responseText)

                dataDisplay = await self.createDataLeaderboards(data, gameID, gtype, amount)

                loop = asyncio.get_running_loop()

                image = await loop.run_in_executor(  # Create image in another thread to prevent blocking
                    None, self.createImage, (dataDisplay)
                )

                with BytesIO() as image_binary:
                    image.save(image_binary, 'PNG')
                    image_binary.seek(0)

                    embed = discord.Embed(
                        title=f"{self.gameFullName[gameID]} leaderboards")

                    file = discord.File(fp=image_binary, filename='stats.png')
                    embed.set_image(url="attachment://stats.png")

                    embed.set_footer(text=f"Requested by {ctx.author}")
                    embed.timestamp = time

                    await ctx.reply(embed=embed, file=file)

            elif responseCode == 404:
                await ctx.reply(embed=simple_embed('Game not supported', f'This game does not have leaderboards! Use `hive help statistics` for usage.', 0xB50000))
                return
            else:
                await ctx.reply(embed=simple_embed('Unknown error.', f'There was a problem with getting statistics, try again later.', 0xB50000))
                return

        except Exception as e:
            print("", exc_info=True)

    async def createText(self, username, data, gameID):

        dataDisplay = {
            "topText": username,
            "special": self.checkIfSpecial(username)
        }
        try:
            if gameID == "wars":
                dxp = data["xp"]
                dplayed = data["played"]
                dvictories = data["victories"]
                dkills = data["kills"]
                ddeaths = data["deaths"]
                dfkills = data["final_kills"]
                dtreasures = data["treasure_destroyed"]

                dataDisplay["items"] = {
                    "Experience": dxp,
                    "Games played": dplayed,
                    "Games won": dvictories,
                    "Games lost": dplayed - dvictories,
                    "Wins/Losses": round(dvictories / (dplayed - dvictories), ndigits=self.roundDataTo),
                    "Winrate %": str(round(dvictories / dplayed * 100, ndigits=self.roundDataTo)),
                    "Kills": dkills,
                    "Deaths": ddeaths,
                    "Kills/Deaths": round(dkills / ddeaths, ndigits=self.roundDataTo),
                    "Kills/Game": round(dkills / dplayed, ndigits=self.roundDataTo),
                    "Final kills": dfkills,
                    "Final kills/Game": round(dfkills / dplayed, ndigits=self.roundDataTo),
                    "Final kills/Death": round(dfkills / ddeaths, ndigits=self.roundDataTo),
                    "Treasures destroyed": dtreasures,
                    "Treasures/Game": round(dtreasures / dplayed, ndigits=self.roundDataTo),
                    "Experience/Game": round(dxp / dplayed, ndigits=self.roundDataTo)
                }
            elif gameID == "dr":
                dxp = data["xp"]
                dplayed = data["played"]
                dvictories = data["victories"]
                dkills = data["kills"]
                ddeaths = data["deaths"]
                dcheckpoints = data["checkpoints"]
                dactivated = data["activated"]

                dataDisplay["items"] = {
                    "Experience": dxp,
                    "Games played": dplayed,
                    "Games won": dvictories,
                    "Games lost": dplayed - dvictories,
                    "Wins/Losses": round(dvictories / (dplayed - dvictories), ndigits=self.roundDataTo),
                    "Winrate %": str(round(dvictories / dplayed * 100, ndigits=self.roundDataTo)),
                    "Kills": dkills,
                    "Deaths": ddeaths,
                    "Kills/Deaths": round(dkills / ddeaths, ndigits=self.roundDataTo),
                    "Kills/Game": round(dkills / dplayed, ndigits=self.roundDataTo),
                    "Checkpoints": dcheckpoints,
                    "Activated": dactivated,
                    "Experience/Game": round(dxp / dplayed, ndigits=self.roundDataTo)
                }
            elif gameID == "hide":
                dxp = data["xp"]
                dplayed = data["played"]
                dvictories = data["victories"]
                dhkills = data["hider_kills"]
                dskills = data["seeker_kills"]
                ddeaths = data["deaths"]

                dataDisplay["items"] = {
                    "Experience": dxp,
                    "Games played": dplayed,
                    "Games won": dvictories,
                    "Games lost": dplayed - dvictories,
                    "Wins/Losses": round(dvictories / (dplayed - dvictories), ndigits=self.roundDataTo),
                    "Winrate %": str(round(dvictories / dplayed * 100, ndigits=self.roundDataTo)),
                    "Hider kills": dhkills,
                    "Seeker kills": dskills,
                    "Deaths": ddeaths,
                    "Kills/Game": round((dhkills + dskills) / dplayed, ndigits=self.roundDataTo),
                    "Experience/Game": round(dxp / dplayed, ndigits=self.roundDataTo)
                }
            elif gameID == "sg":
                dxp = data["xp"]
                dplayed = data["played"]
                dvictories = data["victories"]
                dkills = data["kills"]
                ddeathmatches = data["deathmatches"]
                dcows = data["cows"]
                dcrates = data["crates"]

                dataDisplay["items"] = {
                    "Experience": dxp,
                    "Games played": dplayed,
                    "Games won": dvictories,
                    "Games lost": dplayed - dvictories,
                    "Wins/Losses": round(dvictories / (dplayed - dvictories), ndigits=self.roundDataTo),
                    "Winrate %": str(round(dvictories / dplayed * 100, ndigits=self.roundDataTo)),
                    "Kills": dkills,
                    "Kills/Deaths": round(dkills / (dplayed - dvictories), ndigits=self.roundDataTo),
                    "Kills/Game": round(dkills / dplayed, ndigits=self.roundDataTo),
                    "Deathmateches": ddeathmatches,
                    "Deathmatches %": round(ddeathmatches / dplayed, ndigits=self.roundDataTo),
                    "Crates": dcrates,
                    "Cows": dcows,
                    "Experience/Game": round(dxp / dplayed, ndigits=self.roundDataTo)
                }
            elif gameID == "murder":
                dxp = data["xp"]
                dplayed = data["played"]
                dvictories = data["victories"]
                dkills = data["murders"]
                ddkills = data["murderer_eliminations"]
                dcoins = data["coins"]
                ddeaths = data["deaths"]

                dataDisplay["items"] = {
                    "Experience": dxp,
                    "Games played": dplayed,
                    "Games won": dvictories,
                    "Games lost": dplayed - dvictories,
                    "Wins/Losses": round(dvictories / (dplayed - dvictories), ndigits=self.roundDataTo),
                    "Winrate": str(round(dvictories / dplayed * 100, ndigits=self.roundDataTo)) + "%",
                    "Murders": dkills,
                    "Deaths": ddeaths,
                    "Kills/Deaths": round(dkills / ddeaths, ndigits=self.roundDataTo),
                    "Murderers killed": ddkills,
                    "Experience/Game": round(dxp / dplayed, ndigits=self.roundDataTo),
                }
            elif gameID == "sky":
                print(data)
                dxp = data["xp"]
                dplayed = data["played"]
                dvictories = data["victories"]
                dkills = data["kills"]
                dmchests = data["mystery_chests_destroyed"]
                dores = data["ores_mined"]
                dspells = data["spells_used"]

                dataDisplay["items"] = {
                    "Experience": dxp,
                    "Games played": dplayed,
                    "Games won": dvictories,
                    "Games lost": dplayed - dvictories,
                    "Wins/Losses": round(dvictories / (dplayed - dvictories), ndigits=self.roundDataTo),
                    "Winrate %": str(round(dvictories / dplayed * 100, ndigits=self.roundDataTo)),
                    "Kills": dkills,
                    "Deaths": dplayed - dvictories,
                    "Kills/Deaths": round(dkills / (dplayed - dvictories), ndigits=self.roundDataTo),
                    "Mystery chests": dmchests,
                    "Mystery chests/Game": round(dmchests / dplayed, ndigits=self.roundDataTo),
                    "Ores mined": dores,
                    "Ores/Game": round(dores / dplayed, ndigits=self.roundDataTo),
                    "Spells used": dspells,
                    "Spells/Game": round(dspells / dplayed, ndigits=self.roundDataTo),

                    "Experience/Game": round(dxp / dplayed, ndigits=self.roundDataTo),

                }
        except Exception as e:
            print(f"{username}\n{data}\n{gameID}", exc_info=True)

        return dataDisplay

    async def createDataLeaderboards(self, data, gameID, type, amount):
        if "all" in type:
            type = "all time"
        else:
            type = "monthly"
        dataDisplay = {
            "topText": f"{self.gameFullName[gameID]} {type} leaderboard",
            "valueLeftMargin": 300
        }

        dataDisplay["items"] = {

        }
        if amount > len(data):
            amount = len(data)

        for n in range(amount):
            dataDisplay["items"]["#" + str(data[n]["human_index"]) + " - " + str(
                data[n]["victories"]) + " wins"] = data[n]["username"]

        return dataDisplay


# The setup fucntion below is neccesarry. Remember we give bot.add_cog() the name of the class in this case MembersCog.
# When we load the cog, we use the name of the file.
def setup(client):
    client.add_cog(statsCog(client))
