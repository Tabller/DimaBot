import asyncio
import random
import re
from datetime import datetime, timedelta

import discord
from discord import app_commands, ui
from discord.ext import commands

from src.config import servers_ref, penalty_ref, ui_localization


def parse_time(time_str: str) -> int:
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    match = re.fullmatch(r"(\d+)([smhd])", time_str.lower())
    if not match:
        raise ValueError("moderation_cog, !cage: incorrect time")
    value, unit = match.groups()
    if int(value) < 99999:
        return int(value) * time_units[unit]
    else:
        raise ValueError("moderation_cog, !cage: incorrect time")

class SettingsModal(ui.Modal, title="dimaBot's settings menu"):
    def __init__(self, guild_id: int):
        super().__init__()
        self.server_id = guild_id

        server_dict = servers_ref.child(str(self.server_id)).get()

        self.option_bot_channel_id = ui.TextInput(label='BOT_CHANNEL_ID',
                                                  placeholder=f"{server_dict.get("BOT_CHANNEL_ID")}",
                                                  max_length=128, required=False)
        self.add_item(self.option_bot_channel_id)
        self.option_timeout_channel_id = ui.TextInput(label='TIMEOUT_CHANNEL_ID',
                                                      placeholder=f"{server_dict.get("TIMEOUT_CHANNEL_ID")}",
                                                      max_length=128, required=False)
        self.add_item(self.option_timeout_channel_id)
        self.option_timeout_role_id = ui.TextInput(label='TIMEOUT_ROLE_ID',
                                                   placeholder=f"{server_dict.get("TIMEOUT_ROLE_ID")}",
                                                   max_length=128, required=False)
        self.add_item(self.option_timeout_role_id)
        self.option_prefix = ui.TextInput(label="PREFIX", placeholder=f"{server_dict.get("PREFIX")}",
                                          max_length=128, required=False)

        self.option_lang = ui.TextInput(label="LANGUAGE", placeholder=f"{server_dict.get("LANGUAGE")}", max_length=3,
                                 required=False)
        self.add_item(self.option_lang)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        for option, value in {f"{self.option_bot_channel_id.label}": f"{self.option_bot_channel_id.value}",
                              f"{self.option_timeout_channel_id.label}": f"{self.option_timeout_channel_id.value}",
                              f"{self.option_timeout_role_id.label}": f"{self.option_timeout_role_id.value}",
                              f"{self.option_prefix.label}": f"{self.option_prefix.value}",
                              f"{self.option_lang.label}": f"{self.option_lang.value}"}.items():
            if value == '':
                pass
            else:
                servers_ref.child(str(interaction.guild.id)).update({f"{option}": f"{value}"})
        await interaction.followup.send("ладно")

async def finish_timeout_after(bot, user_id, guild_id, remaining_time):
    """Завершает таймаут через указанное время"""
    try:
        await asyncio.sleep(remaining_time)

        guild = bot.get_guild(int(guild_id))
        if not guild:
            return

        member = guild.get_member(int(user_id))
        role = guild.get_role(int(servers_ref.child(guild_id).get().get('TIMEOUT_ROLE_ID')))

        if (member and role) and (role in member.roles):
            await member.remove_roles(role)
            penalty_ref.child(user_id).delete()
    except Exception as e:
        print(f"finish_timeout_after: {e}")



class ModerationCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    """
    cage
    """
    @commands.hybrid_command(name="cage", with_app_command=True)
    @app_commands.describe(member="user", time="time (s/m/h/d)")
    @commands.has_permissions(administrator=True)
    async def cage(self, ctx: commands.Context, member: discord.Member, time: str, bananas: str = None, *,
                     reason: str = None):
        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"
        server_data = servers_ref.child(str(ctx.guild.id)).get()
        if server_data:
            role_id = server_data.get("TIMEOUT_ROLE_ID")
        else:
            role_id = None

        if role_id:
            role = ctx.guild.get_role(int(role_id))
        else:
            role = None

        if role is None:
            await ctx.send(f'{ui_localization.get("cage").get("cage_no_timeout_role").get(LANG)}')
            return

        if reason is not None:
            if len(reason) > 1024:
                await ctx.reply(f'{ui_localization.get("cage").get("cage_long_reason").get(LANG)}', ephemeral=True)
                return


        if not (bananas is None):
            new_thing = int(bananas)
            if new_thing <= 0 or new_thing > 99999:
                await  ctx.reply(f"{ui_localization.get("cage").get("cage_bananas_limit").get(LANG)}", ephemeral=True)
                return
        else:
            pass



        if role in member.roles:
            await ctx.reply(f"{member.mention} {ui_localization.get("cage").get("cage_already_in").get(LANG)}", ephemeral=True)
            return


        time_in_seconds = parse_time(time)
        if time_in_seconds <= 0:
            await ctx.reply(f"{member.mention} {ui_localization.get("cage").get("cage_incorrect_time").get(LANG)}", ephemeral=True)
            return

        server_dict = servers_ref.child(str(ctx.guild.id)).get()

        try:
            channel = self.client.get_channel(int(server_dict.get("TIMEOUT_CHANNEL_ID")))
        except:
            channel = None


        if not channel:
            message = await ctx.send(
                f"{ui_localization.get("cage").get("cage_no_channel").get(LANG)}")
            return

        try:
            await member.add_roles(role)
            await ctx.reply(f"{ui_localization.get("cage").get("cage_start").get(LANG)} {member.mention}.")
        except Exception as e:
            print(f"moderation_cog, !cage: {e}")
            await ctx.reply(f"{ui_localization.get("cage").get("cage_no_manage_roles").get(LANG)}", ephemeral=True)


        cage_items = {"🍌": {
            "LANG_RU": "бананов",
            "LANG_EN": "bananas"
        }}
        thing = random.choice(*cage_items.keys())
        name = cage_items.get(thing).get(LANG)

        now = datetime.now()
        end_time = now + timedelta(seconds=time_in_seconds)
        unix_timestamp = int(end_time.timestamp())
        start_time_unix_timestamp = int(now.timestamp())

        user_penalty = penalty_ref.child(str(member.id)).get()
        if user_penalty is None:
            penalty_ref.child(str(member.id)).set({'item': f'{bananas}', 'start_time': f"{start_time_unix_timestamp}", 'end_time': f'{unix_timestamp}', 'guild_id': f'{ctx.guild.id}'})

        if channel:
            embed = discord.Embed(
                title=f"{ui_localization.get("cage").get("cage_welcome1").get(LANG)}, {member}",
                description=f"{ui_localization.get("cage").get("cage_welcome2").get(LANG)}",
                color=discord.Color.blurple()
            )


            embed.add_field(name=f"{ui_localization.get("cage").get("cage_time").get(LANG)}", value=f"<t:{unix_timestamp}>")

            if reason:
                embed.add_field(name=f"{ui_localization.get("cage").get("cage_note").get(LANG)}:", value=f"{reason}",
                                inline=False)
                embed.add_field(name=f"{ui_localization.get("cage").get("cage_note_author").get(LANG)}:", value=f"-{ctx.author}")

            if bananas:
                embed.add_field(name=f"{ui_localization.get("cage").get("cage_escape_condition1").get(LANG)}:",
                                value=f"{ui_localization.get("cage").get("cage_escape_condition2").get(LANG)} {new_thing} {name}, {ui_localization.get("cage").get("cage_escape_condition3").get(LANG)} {thing}",
                                inline=False)
            await channel.send(embed=embed)
        else:
            await ctx.send(f"{ui_localization.get("cage").get("cage_channel_deletion").get(LANG)}")
            raise Exception(f"moderation_cog, !клетка: канал удалился")


        await asyncio.sleep(time_in_seconds)

        try:
            await member.remove_roles(role)
            await ctx.send(f"{ui_localization.get("cage").get("cage_escape1").get(LANG)}, {member.mention} {ui_localization.get("cage").get("cage_escape2").get(LANG)}")
            penalty_ref.child(str(member.id)).delete()
        except Exception as e:
            print(f"moderation_cog, !клетка: {e}")
            # await ctx.send(f"у бота нету прав на выдачу ролей!! админы, освободите {member.display_name}")

    """
    Settings
    """

    @app_commands.command(name="settings", description="dimaBot's settings menu")
    @app_commands.checks.has_permissions(administrator=True)
    async def settings(self, interaction: discord.Interaction):
        """Команда открывает настройки бота"""
        await interaction.response.send_modal(SettingsModal(interaction.guild.id))


async def setup(client):
    await client.add_cog(ModerationCog(client))
