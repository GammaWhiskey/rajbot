import json
import re
import os
import time

import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

from roblox_py import Client as RobloxClient

import discord

roblox_client = RobloxClient(cookies=str(os.environ.get("ROBLOX_TOKEN")))

roblox_group_id = os.environ.get("ROBLOX_GROUP_ID")

discord_log_channel_id = os.environ.get("DISCORD_LOG_CHANNEL_ID")
discord_notification_channel_id = os.environ.get("DISCORD_NOTIFICATION_CHANNEL_ID")

async def format_and_shout(client, message):
    # Remove all instances of @everyone / @here, role mentions, and user mentions
    formatted_shout_message = re.sub(r"(@\w+\W?)|(<@(!|&)\w+>\W?)", "", message.content)

    username_to_use = message.author.nick
    if not username_to_use:
        username_to_use = message.author.name

    formatted_shout_message = username_to_use + ": " + formatted_shout_message

    try:
        performance_timer_start = time.perf_counter()
        auth_group = await roblox_client.get_auth_group(roblox_group_id)
        await auth_group.change_shout(formatted_shout_message)
    except:
        embed_var = discord.Embed(title = "Shout Failure", color = discord.Color.dark_red())
        embed_var.set_author(name = username_to_use, icon_url = str(message.author.avatar_url))
        embed_var.add_field(
            name = "Failed to shout message from " + message.channel.name + ".",
            value = formatted_shout_message
        )
        embed_var.set_footer(text="Please report this to SimplestUsername.")
        
        log_channel = client.get_channel(discord_log_channel_id)
        await log_channel.send(embed=embed_var)
        raise
    else:
        embed_var = discord.Embed(title = "Shout Succeeded", color = discord.Color.dark_red())
        embed_var.set_author(name = username_to_use, icon_url = str(message.author.avatar_url))
        embed_var.add_field(
            name = "Shouted message from " + message.channel.name + " successfully.",
            value = formatted_shout_message
        )
        embed_var.set_footer(text="Any issues? Contact SimplestUsername. Elapsed time: " + str(time.perf_counter() - performance_timer_start))
        
        log_channel = client.get_channel(discord_log_channel_id)
        await log_channel.send(embed=embed_var)

class DiscordClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if message.author.bot: 
            return

        if message.channel.id == discord_notification_channel_id:
            await format_and_shout(self, message)

discord_client = DiscordClient()
discord_client.run(os.environ.get("DISCORD_TOKEN"))