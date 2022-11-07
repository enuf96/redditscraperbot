import hikari
import requests
import re
import traceback
import asyncio
import resource.message_channels as message_channels
from datetime import datetime, timezone
from importlib import reload
from os.path import exists

class InvalidRedditType(Exception):
    pass

class RedditWatcher:
    def __init__(self, url: str, postFileName: str, bot: hikari.GatewayBot):
        self.postFileName = "ids/" + postFileName
        self.url = url
        self.bot = bot
        self.headers = { 'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.175 Safari/537.36" }

        if url.startswith("https://api.reddit.com/user"):
            self.type = "u"
        elif url.startswith("https://api.reddit.com/r"):
            self.type = "r"
        else:
            raise InvalidRedditType("The URL is not recognised as a subreddit or an user. Make sure the URL is from the api.")
        
        if not exists(self.postFileName):
            with open(self.postFileName, "w") as f:
                f.write("")


    async def runner(self):
        while True:
            await self.getCurrentPost()
            await asyncio.sleep(15)


    async def correctImageKeys(self, apiDict: dict) -> str:
        '''Makes sure to get the right thumbnail.'''
        keys = {
            "url": "https://i.redd.it",
            "url_overriden_by_dest": "https://i.imgur.com",
            "thumbnail": "https://b.thumbs.redditmedia.com"
        }
        
        for k, v in keys.items():
            key = apiDict.get(k)
            if key and key.startswith(v):
                return key


    async def getCurrentPost(self):
        with open(self.postFileName, "r+") as f:
            content = f.read()
            try:
                request = requests.get(self.url, headers=self.headers).json()
                key_code = request["data"]["children"][0]["data"]
                ts = datetime.fromtimestamp(key_code["created_utc"], tz=timezone.utc)

                if key_code["id"] == content:
                    return # Post already posted. 

                if self.type == "u":
                    body = re.compile(".+?(?=\\n)")       #
                    body = body.findall(key_code["body"]) ## Make sure to not contain the footer with regex.
                    body = body[0]                        #

                    embed = hikari.Embed(
                        title=key_code["link_title"],
                        description=body,
                        url=key_code["link_permalink"],
                        timestamp=ts,
                    )

                    if key_code["link_url"].startswith("https://i.redd.it"):
                        embed.set_image(key_code["link_url"])

                elif self.type == "r":
                    embed = hikari.Embed(
                        title=key_code["title"],
                        description="from other subreddit.",
                        url="https://reddit.com" + key_code["permalink"],
                        timestamp=ts,
                    )

                    if key := await self.correctImageKeys(key_code):
                        embed.set_image(key)

                f.seek(0)
                f.write(key_code["id"])

                await self.sendNewPost(embed)

            except:
                print("Exception:\n\n" + traceback.format_exc())
                await asyncio.sleep(5)
    

    async def sendNewPost(self, embed: hikari.embeds.Embed):
        reload(message_channels)
        for channel in message_channels.channels:
            try:
                await self.bot.rest.create_message(channel, embed)

            except (hikari.errors.NotFoundError, hikari.errors.ForbiddenError):
                await self.removeChannelBlind(channel)
            
            except: # If error is unexpected it is nice to have it documented.
                print(traceback.format_exc())


    async def removeChannelBlind(channel: int) -> None:
        '''Remove channel from array'''
        reload(message_channels)
        my_list = message_channels.channels
        my_list.remove(channel)
        with open("message_channels.py", "w") as f:
            f.write(f"channels = {str(my_list)}")
        reload(message_channels)