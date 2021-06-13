import asyncio
import re
import os

import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

from roblox_py import Client as RobloxClient

import discord

roblox_client = RobloxClient(cookies=str(os.environ.get("ROBLOX_TOKEN")))

roblox_group_id = int(os.environ.get("ROBLOX_GROUP_ID"))

discord_log_channel_id = int(os.environ.get("DISCORD_LOG_CHANNEL_ID"))
discord_notification_channel_id = int(os.environ.get("DISCORD_NOTIFICATION_CHANNEL_ID"))
discord_bot_channel_id = int(os.environ.get("DISCORD_BOT_CHANNEL_ID"))

async def format_and_shout(client: discord.Client, message: discord.Message):
    # Remove all instances of @everyone / @here, role mentions, and user mentions
    formatted_shout_message = re.sub(r"(@\w+\W?)|(<@(!|&)\w+>\W?)", "", message.content)

    # Remove Discord markdown formatting characters that don't have escape characters
    formatted_shout_message = re.sub(r"(?<!\\)\*{1,3}|[_~]{2}", "", formatted_shout_message)

    username_to_use = message.author.nick
    if not username_to_use:
        username_to_use = message.author.name

    if formatted_shout_message == None: # added per suggestion of roblox_py library author
        formatted_shout_message = "None"

    print("Posting group shout by {0}: {1}".format(username_to_use, formatted_shout_message))

    try:
        if len(formatted_shout_message) > 255:
            formatted_shout_message = formatted_shout_message[:255]
            if not await confirm_message_too_long(client, message, formatted_shout_message):
                embed_var = discord.Embed(title = "Shout Cancelled", color = discord.Color.dark_gold())
                embed_var.set_author(name = username_to_use, icon_url = str(message.author.avatar_url))
                embed_var.add_field(
                    name = "Message in " + message.channel.name + " was not shouted due to length.",
                    value = formatted_shout_message
                )
                embed_var.set_footer(text="Any issues? Contact SimplestUsername.")
                
                log_channel = client.get_channel(discord_log_channel_id)
                await log_channel.send(embed=embed_var)
                return

        auth_group = await roblox_client.get_auth_group(roblox_group_id)
        await auth_group.change_shout(formatted_shout_message)
    except Exception as exception:
        embed_var = discord.Embed(title = "Shout Failure", color = discord.Color.dark_red())
        embed_var.set_author(name = username_to_use, icon_url = str(message.author.avatar_url))
        embed_var.add_field(
            name = "Failed to shout message from " + message.channel.name + ".",
            value = formatted_shout_message
        )
        embed_var.add_field(
            name = "The exception encountered is as follows.",
            value = exception
        )
        embed_var.set_footer(text="Please report this to SimplestUsername.")
        
        log_channel = client.get_channel(discord_log_channel_id)
        await log_channel.send(embed=embed_var)

        await message.add_reaction("⚠️")

        raise
    else:
        embed_var = discord.Embed(title = "Shout Succeeded", color = discord.Color.green())
        embed_var.set_author(name = username_to_use, icon_url = str(message.author.avatar_url))
        embed_var.add_field(
            name = "Shouted message from " + message.channel.name + " successfully.",
            value = formatted_shout_message
        )
        embed_var.set_footer(text="Any issues? Contact SimplestUsername.")
        
        log_channel = client.get_channel(discord_log_channel_id)
        await log_channel.send(embed=embed_var)

async def confirm_message_too_long(client: discord.Client, message: discord.Message, shout: str):
    embed_var = discord.Embed(title = "Warning", color = discord.Color.from_rgb(255, 255, 60))
    embed_var.add_field(
        name = "The message you recently sent in " + message.channel.name + " is too long (over 255 characters) to fit as a group shout.",
        value = shout
    )
    embed_var.add_field(
        name = "What would you like to do?",
        value = "⛔: Cancel notification\n✅: Post notification regardless"
    )
    embed_var.set_footer(text="If you do not respond within one minute, the shout WILL be posted.")

    try:
        sent_message: discord.Message = await message.author.send(embed = embed_var)
    except discord.Forbidden:
        embed_var.set_footer(text="If you do not respond within one minute, the shout WILL be posted. Please enable Direct Messages from this server so I can send this to you directly!")

        bot_channel = client.get_channel(discord_bot_channel_id)
        sent_message: discord.Message = await bot_channel.send(embed = embed_var, content = message.author.mention)

    await sent_message.add_reaction("⛔")
    await sent_message.add_reaction("✅")

    def check(reaction: discord.RawReactionActionEvent):
        return reaction.message_id == sent_message.id and reaction.user_id == message.author.id and str(reaction.emoji) in ["⛔", "✅"]

    try:
        reaction: discord.RawReactionActionEvent = await client.wait_for("raw_reaction_add", check = check, timeout = 60)
    except asyncio.TimeoutError:
        await sent_message.edit(embed = discord.Embed(title = "Shout approved.", color = discord.Color.from_rgb(255, 255, 60)))
        return True
    else:
        if str(reaction.emoji) == "⛔":
            await sent_message.edit(embed = discord.Embed(title = "Shout cancelled.", color = discord.Color.from_rgb(255, 255, 60)))
            return False
        else:
            await sent_message.edit(embed = discord.Embed(title = "Shout approved.", color = discord.Color.from_rgb(255, 255, 60)))
            return True

class DiscordClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        if message.channel.id == discord_notification_channel_id:
            await format_and_shout(self, message)

discord_client = DiscordClient()
discord_client.run(os.environ.get("DISCORD_TOKEN"))