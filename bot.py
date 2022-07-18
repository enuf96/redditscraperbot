import os
import hikari
import asyncio
import resource.message_channels as message_channels
from resource.mytoken import tok3n
from requests import get
from importlib import reload
from time import monotonic
from mods import RedditWatcher

if os.name != "nt":
    import uvloop
    uvloop.install()

bot = hikari.GatewayBot(token=tok3n)

ID = hikari.applications.get_token_id(bot._token)
# Pointless dictionary just append to string
cmds ="""```md
# Add:
  * Admin, appends current channel to array.
# Remove:
  * Admin, removes current channel from array.
# Ping:
  * Everyone, returns latency information.
# About:
  * Everyone, returns information about bot.

Reddit bot: https://reddit.com/user/masterhacker_bot
Source code: https://github.com/enuf96/redditscraperbot```"""


async def mentioned(string: str, prefix: str, alias=None) -> bool:
    '''Check if the bot was mentioned'''
    return string == f"<@!{ID}> {prefix}" or string == f"<@{ID}> {prefix}" or string == f"<@{ID}> {alias}" or string == f"<@{ID}> {alias}"


async def status_update() -> None:
    while True:
        _guilds = await bot.rest.fetch_my_guilds()
        g_ext, c_ext = "", ""
        if len(_guilds) != 1:
            g_ext = "s"
        if len(message_channels.channels) != 1:
            c_ext = "s"
        
        try:
            await bot.update_presence(
                activity=hikari.presences.Activity(name=f"{len(_guilds)} guild{g_ext} and {len(message_channels.channels)} channel{c_ext} to send to", type=3),
                status=hikari.presences.Status(hikari.presences.Status.DO_NOT_DISTURB)
                )
        
        except:
            pass
        
        await asyncio.sleep(15)
        reload(message_channels)
        


async def is_admin(guild: hikari.guilds.GatewayGuild, userid: int) -> bool:
    '''Check if user is admin or owner.'''
    if userid == guild.owner_id:
        return True
    else:
        roles = await guild.fetch_roles()
        member = guild.get_member(userid)

        for i in range(0, len(roles)):
            if roles[i].id in member.role_ids:
                if roles[i].permissions & hikari.permissions.Permissions.ADMINISTRATOR:
                    return True

        return False


@bot.listen()
async def on_started(event: hikari.StartedEvent):
    #global redditTask
    #global redditItTask
    global statusupdate_
    #reddit_ = RedditWatcher("https://api.reddit.com/user/masterhacker_bot", "redditID.txt", bot)
    #redditIt_ = RedditWatcher("https://api.reddit.com/r/iiiiiiitttttttttttt/new/", "redditIT_ID.txt", bot)

    statusupdate_ = asyncio.create_task(status_update())
    #redditTask = asyncio.create_task(reddit_.runner())
    #redditItTask = asyncio.create_task(redditIt_.runner())


@bot.listen()
async def on_stop(event: hikari.StoppingEvent):
    #redditTask.cancel()
    #redditItTask.cancel()
    statusupdate_.cancel()


@bot.listen()
async def add_channel(event: hikari.GuildMessageCreateEvent) -> None:
    if event.is_bot or not event.content:
        return

    if await mentioned(event.content, "add"):
        if not await is_admin(event.get_guild(), event.author_id): return

        channel_id = int(event.channel_id)
        my_list = message_channels.channels

        if channel_id not in message_channels.channels:
            my_list.append(channel_id)
            with open("resource/message_channels.py", "w") as f:
                f.write(f"channels = {str(my_list)}")
            
            await event.message.respond(f"Added <#{channel_id}> `({channel_id})` to the channels array.", reply=True)
            reload(message_channels)

        else:
            await event.message.respond(f"Channel already in array.", reply=True)


@bot.listen()
async def remove_channel(event: hikari.GuildMessageCreateEvent) -> None:
    if event.is_bot or not event.content:
        return

    if await mentioned(event.content, "remove"):
        if not await is_admin(event.get_guild(), event.author_id): return

        channel_id = int(event.channel_id)
        my_list = message_channels.channels

        if channel_id in message_channels.channels:
            my_list.remove(channel_id)
            with open("resource/message_channels.py", "w") as f:
                f.write(f"channels = {str(my_list)}")
            
            await event.message.respond(f"Removed <#{channel_id}> `({channel_id})` to the channels array.", reply=True)
            reload(message_channels)

        else:
            await event.message.respond(f"Channel doesn't exist in array.", reply=True)


@bot.listen()
async def ping(event: hikari.GuildMessageCreateEvent):
    if event.is_bot or not event.content:
        return
    
    if await mentioned(event.content, "ping"):
        start = monotonic()
        get("https://api.reddit.com/user/masterhacker_bot")
        reddit_ping = monotonic() - start

        start = monotonic()
        message = await event.message.respond("ey dawg wanna get some ice cream", reply=True)
        api_ping = monotonic() - start

        await message.edit(f"Average shard heartbeat: {bot.heartbeat_latency * 1000:.2f}ms\nReddit HTTP API: {reddit_ping * 1000:.2f}ms\nDiscord HTTP API: {api_ping * 1000:.2f}ms")


@bot.listen()
async def about(event: hikari.GuildMessageCreateEvent):
    if event.is_bot or not event.content:
        return

    if await mentioned(event.content, "about", "help"):
        await event.message.respond(cmds, reply=True)


bot.run()