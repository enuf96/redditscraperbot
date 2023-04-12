import hikari
import requests
import re
import traceback
import asyncio
import resource.message_channels as message_channels
from datetime import datetime, timezone
from importlib import reload
from os.path import exists
from enum import Enum

class enums(Enum):
    USER = 0
    SUBREDDIT = 1

class RedditWatcher:
    def __init__(self, bot: hikari.GatewayBot):
        self.Bot = bot
        self.Headers = { 'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.175 Safari/537.36" }
        self.WatchList = {
            "iiiiiiitttttttttttt": enums.SUBREDDIT,
            "masterhacker_bot": enums.USER
        }

    async def Runner(self):
        while True:
            await self.GetCurrentPost()
            await asyncio.sleep(15)


    async def CorrectImageKeys(self, apiDict: dict) -> str:
        '''Makes sure to get the right thumbnail.'''
        keys = {
            "url": "https://i.redd.it",
            "url_overriden_by_dest": "https://i.imgur.com",
            "thumbnail": "https://b.thumbs.redditmedia.com"
        }
        
        for url_key, image_domain in keys.items():
            key = apiDict.get(url_key)
            if key and key.startswith(image_domain):
                return key


    async def GetCurrentPost(self):
        for Name, Type in self.WatchList.items():
            # Cooldown
            await asyncio.sleep(1)

            if Type == enums.SUBREDDIT:
                TypeVariable = "r"
                GetUrl = f"https://api.reddit.com/{TypeVariable}/{Name}/new"
            elif Type == enums.USER:
                TypeVariable = "user"
                GetUrl = f"https://api.reddit.com/{TypeVariable}/{Name}/"
            
            if not exists(f"ids/{TypeVariable}_{Name}.id"):
                with open(f"ids/{TypeVariable}_{Name}.id", "w") as f:
                    f.write("")

            try:
                Response = requests.get(GetUrl, headers=self.Headers).json()
                KeyCode = Response["data"]["children"][0]["data"]
                Timestamp = datetime.fromtimestamp(KeyCode["created_utc"], tz=timezone.utc)

                with open(f"ids/{TypeVariable}_{Name}.id", "r+") as f:
                    Content = f.read()

                    # If already posted, skip
                    if Content == KeyCode["id"]:
                        continue
                    
                    f.seek(0)
                    f.write(KeyCode["id"])
                
                if Type == enums.USER:
                    Comment = KeyCode["body"]
                    if Name == "masterhacker_bot":
                        Body = re.compile(".+?(?=\\n)") #
                        Body = Body.findall(Comment)    ## Make sure to not contain the footer with regex.
                        Comment = Body[0]               #

                    Embed = hikari.Embed(
                        title=KeyCode["link_title"],
                        description=Comment,
                        url=KeyCode["link_permalink"],
                        timestamp=Timestamp
                    )

                    # TODO: Probably rewrite this and CorrectImageKeys.
                    if KeyCode["link_url"].startswith("https://i.redd.it"):
                        Embed.set_image(KeyCode["link_url"])

                elif Type == enums.SUBREDDIT:
                    Embed = hikari.Embed(
                        title=KeyCode["title"],
                        description=f"from [r/{Name}](http://reddit.com/r/{Name})",
                        url=f"http://reddit.com{KeyCode['permalink']}",
                        timestamp=Timestamp
                    )

                    Image = await self.CorrectImageKeys(KeyCode)
                    if Image:
                        Embed.set_image(Image)

                await self.SendNewPost(Embed)

            except:
                print("GetCurrentPost Exception:\n\n" + traceback.format_exc())
    

    async def SendNewPost(self, embed: hikari.embeds.Embed):
        reload(message_channels)
        for channel in message_channels.channels:
            try:
                await self.Bot.rest.create_message(channel, embed)

            except (hikari.errors.NotFoundError, hikari.errors.ForbiddenError):
                await self.RemoveChannelBlind(channel)
            
            except: # If error is unexpected it is nice to have it documented.
                print(traceback.format_exc())


    async def RemoveChannelBlind(channel: int) -> None:
        '''Remove channel from array'''
        reload(message_channels)
        my_list = message_channels.channels
        my_list.remove(channel)
        with open("message_channels.py", "w") as f:
            f.write(f"channels = {str(my_list)}")
        reload(message_channels)