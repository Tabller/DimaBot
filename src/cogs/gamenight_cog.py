import json
import random
import re
import string
import time
from collections import defaultdict
from copy import deepcopy

import discord
import requests
from discord import app_commands, Color, ui
from discord.ext import commands

from src.config import nights_ref, servers_ref


def iterate(author):
    word = ''
    for i in author:
        if i in '~*_`|>':
            word = word + '\\'
            word = word + i
        else:
            word = word + i
    return word

class GameSubmitSurvey(ui.Modal, title='Предложение игр для Геймнайта', ):
    game1 = ui.TextInput(label='Название первой игры', max_length=63)
    game2 = ui.TextInput(label='Название второй игры', max_length=63, required=False)
    game3 = ui.TextInput(label='Название третьей игры', max_length=63, required=False)
    confirm = ui.TextInput(label='я СОГЛАСЕН что ПРИДЁТСЯ пойти на геймнайт', placeholder="да", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        if self.confirm.value.lower() != "да":
            return
        await interaction.response.defer(ephemeral=True)

        server = servers_ref.child(str(interaction.guild.id))
        server_dict = server.get()
        try:
            target_channel = interaction.client.get_channel(int(server_dict.get("BOT_CHANNEL_ID")))
        except:
            target_channel = None

        if target_channel is None:
            message = await interaction.followup.send("какой же всё таки пипец что бот не настроен... админы напишите `/settings` и добавьте BOT_CHANNEL_ID (основной канал где бот будет писать)")
            return

        submitted_games = []
        for _ in [self.game1.value, self.game2.value, self.game3.value]:
            result = ''
            if len(str(_)) < 64:
                pattern = "(?P<url>https?://[^\s]+)"
                r1 = re.split(pattern, _)
                r2 = re.findall(pattern, _)
                for item in r1:
                    if item in r2:
                        result = result + '<' + item + '>'
                    else:
                        result = result + item
            submitted_games.append(_)
        submitted_games = [game for game in submitted_games if game]

        for game in submitted_games:
            nights_server = nights_ref.child(str(interaction.guild.id))
            user_data = nights_server.child(str(interaction.user.id)).get() or {}
            game_count = len(user_data.keys())
            if user_data is None:
                nights_server.child(str(interaction.user.id)).set({
                    '-L' + str(int(time.time() * 1000)): str(game).replace('\n', '')  # Add the new game with a timestamp
                })
            else:
                if game_count >= 3:
                    summarize = [key for key in user_data.keys()]
                    oldest_game = min(summarize)
                    nights_server.child(str(interaction.user.id)).update({
                        oldest_game: None,
                        '-L' + str(int(time.time() * 1000)): str(game).replace('\n', '')
                    })

                else:
                    # If the user has less than 3 games, add the new game
                    nights_server.child(str(interaction.user.id)).update({
                        '-L' + str(int(time.time() * 1000)): str(game).replace('\n', '')
                        # Add the new game with a timestamp
                    })

        display_namee = iterate(interaction.user.display_name)
        embed1 = discord.Embed(description=f'**{display_namee}** предложил следующие игры: **{', '.join(map(str, submitted_games))}**',
                               colour=discord.Colour(int('ec5353', 16)))
        message = await target_channel.send(embed=embed1)
        message_id = message.id
        await message.add_reaction('tomatjret:1098375901248487424')

class GamenightCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="gamenight_list", description="Просмотреть список и возможность скачать его в виде json-file")
    async def gamenight_list(self, interaction: discord.Interaction):
        """Команда, которая генерирует и список, и json-file списка."""

        """Генерация json-file списка"""
        nights_data = nights_ref.get()
        all_games = defaultdict(dict)
        for server_id, server_data in nights_data.items():
            if str(server_id) != str(interaction.guild.id):
                continue
            for user_id, games in server_data.items():
                if user_id == 'BIN':
                    continue
                all_games[user_id].update(games)


        all_games = dict(all_games)

        games_list = []
        if all_games:
            count = 1
            for user_id, games in all_games.items():
                for game in games.values():
                    data_object = {
                        "fastid": f"{count}",
                        "id": str(random.random()),
                        "amount": 1,
                        "name": game,
                        "investors": []
                    }
                    games_list.append(data_object)
                    count += 1

        json_str = json.dumps(games_list, ensure_ascii=False, indent=2)

        bin_name = nights_ref.child(str(interaction.guild.id)).child("BIN").get() # 15 символов

        filename = "gamenight.json"

        response = requests.post(
            f"https://filebin.net/{bin_name}/{filename}",
            data=json_str.encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 201:
            file_url = f"https://filebin.net/{bin_name}/{filename}"
        else:
            print(f"{response.status_code}, {response.text}")

        """Генерация списка"""
        message = ''
        if all_games:
            for user_id, games in all_games.items():
                for game in games.values():
                    message += f"{game}\n"

            embed = discord.Embed(
                title="Список возможных игр Геймнайта:",
                description=f"{message}",
                color=Color.gold(),
            )


            class DownloadButton(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=None)
                    self.add_item(discord.ui.Button(
                        label='скачать json для вставки в рулетку',
                        style=discord.ButtonStyle.gray,
                        url=str(file_url),
                        emoji="🐓",
                    ))

                async def respond(self, button_interaction: discord.Interaction):
                    await button_interaction.response.defer()

            await interaction.response.send_message(embed=embed, view=DownloadButton())
        else:
            await interaction.response.send_message('Лист пуст')


    @app_commands.command(name="gamenight_start", description="Начать Геймнайт и запустить предложку игр")
    @app_commands.checks.has_permissions(administrator=True)
    async def gamenight_start(self, interaction: discord.Interaction):
        await interaction.response.defer()
        nights_data = nights_ref.get()
        if not (nights_data.get(str(interaction.guild.id))):
            night_server = nights_ref.child(str(interaction.guild.id))
            characters = string.ascii_lowercase + string.digits
            result = ''.join(random.choice(characters) for _ in range(15))
            night_server.set({"BIN": f"{result}"})
            embed = discord.Embed(description="рулетка инициализирована предлагайте игры", color=Color.green())
            class SubmitButton(discord.ui.View):
                @discord.ui.button(label='предложить игру', style=discord.ButtonStyle.success, emoji="😂")
                async def respond(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    new_nights_data = nights_ref.get()
                    if new_nights_data.get(str(button_interaction.guild.id)):
                        await button_interaction.response.send_modal(GameSubmitSurvey())
                    else:
                        await button_interaction.response.send_modal("геймнайт уже закончился", ephemeral=True)
            await interaction.followup.send(embed=embed, view=SubmitButton(timeout=None))
        else:
            await interaction.followup.send("ну геймнайт уже начат у твоего сервера", ephemeral=True)

    @app_commands.command(name="gamenight_end", description="Закончить предложку Геймнайта")
    @app_commands.checks.has_permissions(administrator=True)
    async def gamenight_end(self, interaction: discord.Interaction):
        nights_data = nights_ref.get()
        if nights_data.get(str(interaction.guild.id)):
            nights_ref.child(str(interaction.guild.id)).delete()
            embed = discord.Embed(description="предложка всё! больше нельзя предлагать игры", color=Color.red())
        else:
            embed = discord.Embed(description="ау геймнайта ещё нету")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="gamenight_gamedelete", description="Удалить СВОЮ игру из Геймнайта")
    async def gamenight_gamedelete(self, interaction: discord.Interaction, suggestion: str):
        await interaction.response.defer()
        user_data = nights_ref.child(str(interaction.guild.id)).child(str(interaction.user.id)).get()
        result = ''
        if user_data is not None:
            t_list = deepcopy(user_data)
            pattern = "(?P<url>https?://[^\s]+)"
            r1 = re.split(pattern, suggestion)
            r2 = re.findall(pattern, suggestion)
            for item in r1:
                if item in r2:
                    result = result + '<' + item + '>'
                else:
                    result = result + item
            matching_keys = [key for key, v in t_list.items() if v == result]
            if matching_keys:
                t_list.pop(matching_keys[0])
                game_path = f"{str(interaction.guild.id)}/{str(interaction.user.id)}/{matching_keys[0]}"
                nights_ref.child(game_path).delete()
                await interaction.followup.send(f'Успешно удалён элемент {suggestion}.')
            else:
                await interaction.followup.send(f'Элемент не найден в вашем списке...')
        else:
            await interaction.followup.send(f'User не найден в списке...')

    @gamenight_gamedelete.error
    async def game_delete_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(error)

async def setup(client):
    await client.add_cog(GamenightCog(client))
