import copy
import itertools
from http.client import responses
import string
import discord
import re
import requests
import asyncio
import os
import firebase_admin
import random
import json
import time
from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from io import StringIO
from discord import ui, Interaction, Color, Guild
from discord.ext.commands import has_any_role, param
from firebase_admin import db, credentials
from discord.ext import commands, tasks
from dotenv import load_dotenv
from discord.ui import Select
from discord import app_commands
from collections import defaultdict
from google.api_core.operations_v1.operations_client_config import config


"""
Env Variables и прочие вещи (базы данных)
"""
LOCALIZATION_DICT = {} # Here goes all localizations (maybe in some distant future).
WELCOME_MESSAGE_EN = "Hello! it looks like ur trying to install dimabot on your server (or someone is trying to), however, itz not working properly yet vro... owner or any admin should probably configure bot's settings with a command `/settings`\ncheers!"
FEEDBACK_CHANNEL_ID = os.environ['FEEDBACK_CHANNEL_ID'] # ID канала с обратной связью.
PREFIX = '!'

service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
service_account_dict = json.loads(service_account_json)
cred = credentials.Certificate(service_account_dict)
firebase_admin.initialize_app(cred, {
      'databaseURL': f'{os.getenv("LINK_DATABASE")}'
  })

nights_ref = db.reference('nights')
economy_ref = db.reference('economy')
inventory_ref = db.reference('inventory')
penalty_ref = db.reference('penalty')
servers_ref = db.reference('servers')

if nights_ref.get() is None:
    server = nights_ref.child("SERVER_ID")
    server.set({"BIN": "BIN_ID",
                "USER_ID1": "GAME2",
                "USER_ID2": "GAME1"})
elif economy_ref.get() is None:
    user = economy_ref.child("USER_ID1")
    user.set({"coins": "0"})
elif inventory_ref.get() is None:
    user = economy_ref.child("USER_ID1")
elif penalty_ref.get() is None:
    user = penalty_ref.child("USER_ID1")
    user.set({"penalty": "1"})
elif servers_ref.get() is None:
    server = servers_ref.child("SERVER_ID")
    server.set({'PREFIX': f'{PREFIX}',
                'TIMEOUT_CHANNEL_ID': 'None',
                'TIMEOUT_ROLE_ID': 'None',
                'BOT_CHANNEL_ID': 'None'})
else:
    pass

"""
Инициализация бота
"""

load_dotenv(dotenv_path='/root/DimaBot/.env')

intents = discord.Intents.all()
intents.message_content = True

async def get_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or("!")(bot, message)
    prefix = str(servers_ref.child(str(message.guild.id)).child("PREFIX").get())
    if prefix is None or prefix == '':
        return commands.when_mentioned_or("!")(bot, message)
    return commands.when_mentioned_or(prefix)(bot, message)

client = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

"""
События и Задания
"""

favourite_games = itertools.cycle(["Hollow Knight", "Celeste", "Undertale", "Deltarune", "Transformice", "Slime Rancher", "Don't Starve Together", "Stardew Valley", "Roblox", "Geometry Dash", "Coromon", "Castle Crashers", "Minecraft", "Terraria", "Lethal Company", "Starbound", "Streets of Rogue", ""])
@tasks.loop(seconds=60)
async def presence_loop():
    await client.change_presence(activity=discord.Game(next(favourite_games)))

@client.event
async def on_ready():
    """Функция, срабатывающая при включении бота"""
    print(f'Bot {client.user} is online.')
    client.loop.create_task(periodic_task())
    try:
        synced = await client.tree.sync()
        print(f'Synced {len(synced)} interaction command(s).')
    except Exception as exception:
        print(exception)

    presence_loop.start()

@client.event
async def on_guild_join(guild: Guild):
    servers_data = servers_ref.get()
    if not (str(guild.id) in servers_data):
        server = servers_ref.child(str(guild.id))
        server.set({'PREFIX': f'{PREFIX}', # Префикс бота.
                    'TIMEOUT_CHANNEL_ID': 'None', # ID канала для отправки в таймаут.
                    'TIMEOUT_ROLE_ID': 'None', # ID роли, которая выдаётся при таймауте.
                    'BOT_CHANNEL_ID': 'None'}) # ID технического канала, куда будут присылаться некоторые сообщения от бота (если это необходимо)
        owner = await client.fetch_user(guild.owner.id)

        if owner is not None:
            if owner.dm_channel is None:
                await owner.create_dm()
            await owner.dm_channel.send(WELCOME_MESSAGE_EN)
    else:
        pass

@client.event
async def on_guild_remove(guild):
    servers_data = servers_ref.get()
    if str(guild.id) in servers_data:
        servers_ref.child(str(guild.id)).delete()
        nights_ref.child(str(guild.id)).delete()


@client.event
async def on_message(message):
    user_data = economy_ref.child(str(message.author.id)).get()
    if user_data is None:
        economy_ref.child(str(message.author.id)).set({
            'coins': 0
        })
    else:
        current_coins = user_data['coins']
        economy_ref.child(str(message.author.id)).set({
            'coins': current_coins + 1
        })

    await client.process_commands(message)

"""
Команды бота
"""

@client.hybrid_command()
async def test(ctx, *, arg):
    await ctx.send(arg)

placeholder_dict = {}
game_list = []

class Menu(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

class SettingsModal(ui.Modal, title="dimaBot's settings menu"):
    def __init__(self, guild_id: int):
        super().__init__()
        self.server_id = guild_id

        server_dict = servers_ref.child(str(self.server_id)).get()

        self.option_bot_channel_id = ui.TextInput(label='BOT_CHANNEL_ID', placeholder=f"{server_dict.get("BOT_CHANNEL_ID")}", max_length=128, required=False)
        self.add_item(self.option_bot_channel_id)
        self.option_timeout_channel_id = ui.TextInput(label='TIMEOUT_CHANNEL_ID', placeholder=f"{server_dict.get("TIMEOUT_CHANNEL_ID")}", max_length=128, required=False)
        self.add_item(self.option_timeout_channel_id)
        self.option_timeout_role_id = ui.TextInput(label='TIMEOUT_ROLE_ID', placeholder=f"{server_dict.get("TIMEOUT_ROLE_ID")}", max_length=128, required=False)
        self.add_item(self.option_timeout_role_id)
        self.option_prefix = ui.TextInput(label="PREFIX", placeholder=f"{server_dict.get("PREFIX")}", max_length=128, required=False)
        self.add_item(self.option_prefix)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        for option, value in {f"{self.option_bot_channel_id.label}": f"{self.option_bot_channel_id.value}",
                              f"{self.option_timeout_channel_id.label}": f"{self.option_timeout_channel_id.value}",
                              f"{self.option_timeout_role_id.label}": f"{self.option_timeout_role_id.value}",
                              f"{self.option_prefix.label}": f"{self.option_prefix.value}"}.items():
            if value == '':
                pass
            else:
                servers_ref.child(str(interaction.guild.id)).update({f"{option}": f"{value}"})
        await interaction.followup.send("ладно")
                

@client.tree.command(name="settings", description="dimaBot's settings menu")
@commands.has_permissions(administrator=True)
async def settings(interaction: discord.Interaction):
    await interaction.response.send_modal(SettingsModal(interaction.guild.id))


@client.command()
async def help(ctx, command: str = None, member: discord.Member = None):
    LANG = "LANG_RU"
    if member == None:
        member = ctx.author

    name = member.display_name
    pfp = member.display_avatar

    commands_gamenight = {
        "gamenight_start": {'LANG_RU': ["```Команда создаёт ивент Геймнайт (только админы могут использовать эту команду). При создании ивента появится сообщение бота с кнопкой, нажав которую можно будет предложить от 1 до 3 игр. Выбор игры в которую захочется поиграть происходит вручную (через какие-нибудь сайты с рулетками)```",
                                        None,
                                        {"/gamenight_start": "Запускает Геймнайт"},
                                        None],
                            'LANG_EN': 'placeholder'},
        "gamenight_list": {'LANG_RU': ["```Посмотреть список предложенных игр для Геймнайта и возможность скачать json-file```",
                                       None,
                                       {"/gamenight_list": "Показывает список игр, с приложением в виде файла-json"},
                                        None],
                           'LANG_EN': 'placeholder'},
        "gamenight_end": {'LANG_RU': ["```Команда закрывает предложение игр для Геймнайта и сам ивент (админы могут только)```",
                                        None,
                                        {"/gamenight_end": "Объявляет конец Геймнайта"},
                                        None],
                            'LANG_EN': 'placeholder'},
        "gamenight_gamedelete": {'LANG_RU': ["```Удалить СВОЮ игру из списка предложенных игр Геймнайта.```",
                                        {"[suggestion]": "Предложенная вами игра в списке игр."},
                                        {"/gamenight_gamedelete `suggestion:game1`": "Команда удаляет из списка игр вашу игру `game1`"},
                                        None],
                            'LANG_EN': 'placeholder'}
    }
    commands_rpg = {
        "balance": {'LANG_RU': ["```Команда открывает ваш инвентарь, где показывается баланс (монетки), вещи (если имеются). При наличии нескольких страниц инвентаря, их можно листать с помощью кнопок```",
                                None,
                                {"!balance": "Проверяет свой карман (на наличие денег или предметов)", "!balance @user": "Проверяет чужой карман через упоминание пользователя (на наличие денег или предметов)", "!balance 123456789": "Проверяет чужой карман через ID пользователя (на наличие денег или предметов)"},
                                {"[user]": "Упоминание (@user) или же его числовое ID"}
                                ],
                            'LANG_EN': 'placeholder'},

        "fish": {'LANG_RU': ["```Рыбалка симулятор```",
                            None,
                            {"!fish": "Команда запускает мини-игру рыбалку"},
                            None],
                            'LANG_EN': 'placeholder'},
        "sell": {'LANG_RU': ["```Команда позволяет продать предмет или весь ваш инвентарь```",
                            {"[:emoji:]": "Эмодзи, например 🐟", "[inventory]": "Слово inventory даст вам продать весь ваш инвентарь"},
                            {"!sell 🍌": "Команда продаст банан из вашего инвентаря (если он есть)", "!sell inventory": "Команда продаст весь ваш инвентарь"},
                            None],
                            'LANG_EN': 'placeholder'},
        "leaderboard": {'LANG_RU': ["```Просмотр локальной или глобальной таблицы монет. В выпадающем списке необходимо выбрать уровень просмотра (локальный или глобальный)```",
                            None,
                            {"/leaderboard": "Команда показывает выбранный лидерборд"},
                            None],
                            'LANG_EN': 'placeholder'},
        "shop": {'LANG_RU': ["```Просмотр магазина, который обновляется каждые 6 часов.```",
                            None,
                            {"!shop": "Команда показывает меню магазина"},
                            None],
                            'LANG_EN': 'placeholder'},
        "craft": {'LANG_RU': ["```Команда создает предмет, если рецепт (те эмодзи, которые вы отправили) окажется верным.```",
                            {"[:emoji1:]": "Первый эмодзи, например 🐟", "[:emoji2:]": "Второй эмодзи, например 🐡"},
                            {"!craft 🐟🐡": "Команда может быть скрафтит что-то из двух предметов!", "!craft 🎩🍌👢": "Команда может быть скрафтит что-то из трёх предметов!"},
                            {"[:emoji3:]": "Третий эмодзи, например 🎩"}],
                            'LANG_EN': 'placeholder'},
        "pin": {'LANG_RU': ["```Команда позволяет пригвоздить предмет, чтобы его невозможно было продать, или наоборот, отгвоздить его, чтобы его можно было продать.```",
                            {"[:emoji:]": "Эмодзи, например 🍌"},
                            {"!pin 🍌": "Команда пригвоздит/отгвоздит предмет, чтобы его было нельзя/можно продать."},
                            None],
                            'LANG_EN': 'placeholder'},
        "info": {'LANG_RU': ["```Команда позволяет узнать некоторую информацию о предмете, находящегося в вашем инвентаре. Показывает название предмета, дату получения и краткую информацию.```",
                           {"[:emoji:]": "Эмодзи, например 🐟"},
                            {"!info 🐟": "Команда покажет информацию об этом предмете, если он есть у вас в инвентаре."},
                            None],
                            'LANG_EN': 'placeholder'},
        "use": {'LANG_RU': ["```Команда позволяет использовать указанный предмет в вашем инвентаре.```",
                           {"[:emoji:]": "Эмодзи, например 👢"},

                            {"!info 👢": "Команда использует этот предмет и если у него есть применение (не все предметы можно использовать), то что-то произойдёт."},
                            None],
                            'LANG_EN': 'placeholder'},
    }
    commands_admin = {
        "клетка": {'LANG_RU': ["```Команда позволяет отправить человека в подобие таймаута. Для использования этой команды необходимо настроить в /settings следующие параметры: TIMEOUT_CHANNEL_ID - айди канала, который будет доступен людям с таймаутом, TIMEOUT_ROLE_ID - роль, которая будет даваться людям с таймаутом. Вы сами выставляете ограничения у роли и у канала. По задумке, команда на время отправляет пользователя в специальный канал, чтобы тот подумал о своём поведении (или до тех пор, пока он не почистит N количество бананов, но это опционально). ```",
                            {"[@юзер]": "Упоминание пользователя", "[s/m/h/d]": "Время, например 50s или 20d или 3h (50 секунд или 20 дней или 3 часа)."},
                            {"!клетка member:@dummy#9470 time:5s": "Команда отправит участника @dummy#9470 в таймаут на 5 секунд.", "!клетка member:@dummy#9470 time:3d bananas:50": "Команда отправит участника @dummy#9470 в таймаут на 3 дня, НО он может выбраться досрочно, если почистит 50 бананов.", "!клетка member:@dummy#9470 time:5s reason:ну отдохни на водах": "Команда отправит участника @dummy#9470 в таймаут на 5 секунд, также в сообщении будет указана причина отправки в таймаут."},
                            {"[бананы]": "Количество бананов, которое необходимо почистить, чтобы досрочно выбраться из таймаута. Например 50.", "[причина]": "Текст причины, за которую пользователь отправлен в таймаут (в том числе пользователю будет видно, кто отправил в таймаут)"}],
                            'LANG_EN': 'placeholder'},
        "settings": {'LANG_RU': ["```Команда позволяет настроить бота (нужные айди каналов и ролей). Следующие поля можно настроить:\nBOT_CHANNEL_ID - Канал, где бот будет отправлять некоторые сообщения-оповещения (если это необходимо некоторым командам, данный айди пока что используется только в команде /gamenight_start, смотрите help по ней)\nPREFIX - Префикс бота.\nTIMEOUT_CHANNEL_ID - Канал для таймаутов. По задумке (вы можете сделать иначе) в этот канал должна иметь доступ только одна роль, она может туда писать, но не может просматривать остальные каналы вашего сервера (Канал используется в команде /клетка, смотрите help по ней).\nTIMEOUT_ROLE_ID - Роль, которая имеет доступ к ранее упомянутому каналу, по сути таймаут-роль (выдаётся пользователям с помощью команды /клетка, смотрите help по ней).```",
                            None,
                            {"/settings": "Команда запускает меню настройки."},
                            None],
                            'LANG_EN': 'placeholder'},
    }

    commands_other = {
        "feedback": {'LANG_RU': ["```Команда отправить фидбек о боте (ваши идеи, впечатления и так далее). Создатель бота может ответить на сообщение.```",
                            {"[текст]": "Текст, который отправится создателю бота."},
                            {"!feedback ну короче жду бесплатный бургер": "Команда отправит сообщение 'ну короче жду бесплатный бургер' создателю бота."},
                            None],
                            'LANG_EN': 'placeholder'},

        "meme": {'LANG_RU': ["```Команда отправляет рандомный мем из коллекции.```",
                            None,
                            {"!meme": "Отправляет рандомный мем из коллекции."},
                            None],
                            'LANG_EN': 'placeholder'},
        "test": {'LANG_RU': ["```Команда повторяет за пользователем всё, что он напишет.```",
                            {"[сообщение]": "Текст, который вы напишите."},
                            {"!test привет": "Бот отправит сообщение 'привет'.", "/test arg:hello": "Бот отправит сообщение 'hello'."},
                            None],
                            'LANG_EN': 'placeholder'}
    }

    if command is None:
        embed = discord.Embed(title=f'Стандартные команды',
                              colour=discord.Colour(int('a970ff', 16)))
        embed.set_author(name=f"димабот ft. {member.guild.name}",icon_url="https://imgur.com/T9qLfHj.png")

        embed.add_field(name="Геймнайт", value=f"{str("".join([f"`{i}`\n" for i in commands_gamenight.keys()]))}", inline=True)
        embed.add_field(name="Экономика", value=f"{str("".join([f"`{i}`\n" for i in commands_rpg.keys()]))}", inline=True)
        embed.add_field(name="Администрация", value=f"{str("".join([f"`{i}`\n" for i in commands_admin.keys()]))}", inline=True)
        embed.add_field(name="Другие", value=f"{str("".join([f"`{i}`\n" for i in commands_other.keys()]))}", inline=True)

        view = Menu()
        view.add_item(
            discord.ui.Button(label='Twitch Channel', style=discord.ButtonStyle.link,
                              url='https://www.twitch.tv/mrtomit'))
        await ctx.send(embed=embed, view=view)
    else:
        new_command = command.replace("/", "").replace("!", "")
        parse_ = [commands_gamenight, commands_rpg, commands_admin, commands_other]
        for i, d in enumerate(parse_, 1):
            if new_command in d:
                embed = discord.Embed(title=f'{command}', description=f"{d[new_command][LANG][0]}")
                if not (d[new_command][LANG][1] is None):
                    embed.add_field(name="Следующие параметры НЕОБХОДИМЫ:", value=f"{str("".join([f"`{i} -- {j}`\n" for i, j in d[new_command][LANG][1].items()]))}", inline=False)
                if not (d[new_command][LANG][3] is None):
                    embed.add_field(name="Следующие параметры ОПЦИОНАЛЬНЫ:", value=f"{str("".join([f"`{i} -- {j}`\n" for i, j in d[new_command][LANG][3].items()]))}", inline=False)
                embed.add_field(name="Пример использования:", value=f"{str("".join([f"{i}\n{j}\n\n" for i, j in d[new_command][LANG][2].items()]))}", inline=False)
                embed.set_author(name=f"димабот помощник")
                await ctx.send(embed=embed)
                return
        await ctx.send("увы, такой команды нету")

@client.tree.command(name="gamenight_list", description="Просмотреть список и возможность скачать его в виде json-file")
async def gamenight_list(interaction: discord.Interaction):
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

@client.tree.command(name="gamenight_start", description="Начать Геймнайт и запустить предложку игр")
@commands.has_permissions(administrator=True)
async def gamenight_start(interaction: discord.Interaction):
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

@client.tree.command(name="gamenight_end", description="Закончить предложку Геймнайта")
@commands.has_permissions(administrator=True)
async def gamenight_end(interaction: discord.Interaction):
    nights_data = nights_ref.get()
    if nights_data.get(str(interaction.guild.id)):
        nights_ref.child(str(interaction.guild.id)).delete()
        embed = discord.Embed(description="предложка всё! больше нельзя предлагать игры", color=Color.red())
    else:
        embed = discord.Embed(description="ау геймнайта ещё нету")
    await interaction.response.send_message(embed=embed)

@client.tree.command(name="gamenight_gamedelete", description="Удалить СВОЮ игру из Геймнайта")
async def gamenight_gamedelete(interaction: discord.Interaction, suggestion: str):
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
async def game_delete_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(error)

@client.hybrid_command()
async def feedback(ctx, *, text):
    message_time = ctx.message.created_at
    author = ctx.author
    jump_url = ctx.message.jump_url
    channel = client.get_channel(ctx.channel.id) if hasattr(ctx.channel, 'name') else 'DM'
    embed = discord.Embed(description=text, title="Фидбек ft. Димабот").set_footer(text=ctx.author.display_name,
                                                                                   icon_url=ctx.author.avatar.url)

    class AnswerForm(ui.Modal, title='Ответ на входящий фидбек'):
        Field = ui.TextInput(label="Текст")

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            response = self.Field.value
            embed4 = discord.Embed(description=f'Ответ: {response}')
            embed4.add_field(name=" ", value=f"[Ссылка на сообщение]({jump_url})", inline=False)
            embed4.set_footer(text=f"{interaction.user.display_name} ответил на фидбек: {message_time.strftime("%d.%m.%Y")} от {author}", icon_url=interaction.user.avatar.url)
            await channel.send(embed=embed4)


    class AnswerButton(discord.ui.View):
        @discord.ui.button(label='ответить', style=discord.ButtonStyle.success)
        async def respond3(self, interaction: discord.Interaction, item):
            await interaction.response.send_modal(AnswerForm())
       #    await interaction.edit_original_response(view=None)
    send_feedback = await client.get_channel(int(FEEDBACK_CHANNEL_ID)).send(embed=embed,
                                                                            view=AnswerButton(timeout=None))

    await ctx.send('фидбек отправлен (наверное)')

'''
Секция с типичными командами использования
'''

# Инвертирует игровое поле рыбной мини-игры
async def id0use(ctx, item):
    user_id = ctx.author.id
    inventory_data = inventory_ref.child(str(user_id)).get()

    ref = db.reference(f'inventory/{user_id}/effects')
    current = ref.get()


    if inventory_data is None:
       inventory_ref.child(str(ctx.author.id)).set({"effects": "boot"})
    elif current:
        new_value = f"{current};boot"
        ref.set(new_value)
    else:
        inventory_ref.child(str(ctx.author.id)).update({"effects": "boot"})

    dictionary = {}
    for item_name, quantity in inventory_data.items():
        dictionary[item_name] = quantity

    global cool_item_name

    what_to_delete = {}
    for item_name, quantity in dictionary.items():
        if '👢' in item_name:
            if not ('📌' in item_name):
                what_to_delete[item_name] = quantity
                cool_item_name = copy.deepcopy(item_name)
    pattern = r'[0-9]'
    new_string = re.sub(pattern, '', item)

    print(what_to_delete)

    first_way = items.get(item)
    if first_way:
        inventory_path = f"{user_id}/{cool_item_name}"
        inventory_ref.child(inventory_path).delete()
        print('first')
        return

    try:
        for key, val in what_to_delete.items():
            if str(item) == str(val) or str(key) == str(item):
                inventory_path = f"{user_id}/{key}"
                inventory_ref.child(inventory_path).delete()
                return

    except:
        print("ponos")



    embed = discord.Embed(title=f'Карман Игрока {ctx.author.display_name}',
                          colour=discord.Colour(int('5BC1FF', 16)))
    embed.add_field(name=f"",
                    value=f"Вы надели себе на голову 👢. Что-то поменялось, но вы не можете сказать, что именно...")

    await ctx.send(embed=embed)

async def id26use(ctx, item):
    user_id = ctx.author.id
    inventory_data = inventory_ref.child(str(user_id)).get()

    ref = db.reference(f'inventory/{user_id}/fishing_location')
    current = ref.get()

    locations_available = ["спокойный океан", "попасити 2029 год"]
    await ctx.send(
        f"привет, {ctx.author.display_name}! как капитан корабля ты можешь поехать в:\n" +
        "\n".join([f"{name}" for name in locations_available])
    )

    msg = await ctx.send('пиши имя места и поплывём')

    def check(m):
        return m.author == ctx.author and m.content in locations_available

    try:
        response = await client.wait_for('message', check=check, timeout=30)

        if inventory_data is None:
           inventory_ref.child(str(ctx.author.id)).set({"fishing_location": "boot"})
        elif current:
            new_value = f"{response.content}"
            ref.set(new_value)
        else:
            inventory_ref.child(str(ctx.author.id)).update({"fishing_location": f"{response.content}"})
        await ctx.send(f"ура мы плывём в {response.content}")
    except asyncio.TimeoutError:
        await ctx.send("ты чет призадумался, попробуй лучше снова")




'''
Секция со словарём предметов
Формат: Множитель, слово, название предмета, описание предмета, функция использования, эмодзи предмета, стандартная цена в магазине;
'''

items = {
            '👢': [1, "монет", "грязный ботинок", "Грязные ботинки штамповали тысячами в Австралии. Неизвестно почему, но все они оказались в море. Спасите морской биоценоз — соберите их все!", id0use, '👢', "6"],
            '🐟': [1.1, "см", "карась","Карась является самым частовречающимся представителем в здешних водах. Скажите ему привет!", "func", '🐟', "51"],
            '🐠': [1.45, "см", "брат карася","Брат Карася не знает, что у него есть брат. Похоже, тот отбился от косяка... Какая досада!", "func", '🐠', "62"],
            '🐡': [1.28, "см", "рыба агу ага","Это удивительная рыба Агу Ага, о ней мало что известно человечеству.", "func", '🐡', "73"],
            '🪼': [1.76, "см", "медуза крутая","Нередко медузы считаются крутыми, поскольку технически бессмертны (кроме того видоса про черепаху)", "func", '🪼', "83"],
            '🦐': [1.2, "см", "креветочка","Эта креветочка такая милая :)", "func", '🦐', "56"],
            '🐙': [2.3, "см", "разрушитель три тысячи","Ну, не такой уж и страшный.", "func", '🐙', "290"],
            '🦈': [3.23, "см", "Я АКУЛА","ААААААААААА ЛАДНО", "func", '🦈', "430"],
            '🐚': [1.21, "монет", "плавающая ракушка","Говорят, что через такие можно услышать море. Хотя, мы итак рядом с морем, чтобы его слушать.", "func", '🐚', "48"],
            '🍌': [1, "монет", "банано","Кто-то небрежно очистил банан от кожуры. Интересно, их действительно собирают с пальм?", "func", '🍌', "25"],
            '🤖': [5.1, "монет", "петя умный","Петя версия v1. Ничего не делает. Зато круто выглядит.", "func", '🤖', "200000"],
            '💩': [1, "монет", "мусор (говно)","Ну и что за хрень...", "func", '💩', "2"],
            '🎩': [2.45, "монет", "шляпникус","Я не знаю, что это, но это точно не из нашего мира. Может быть, оно обладает каким-либо функционалом? Или используется для чего-то? Кто знает...", "Перемещает вас в рандомную локацию или даёт рандомный статусный эффект", '🎩', "872"],
            '🧦': [1.05, "монет", "грязные носки (братья грязного ботинка)","Грязные носки не штамповали тысячами, однако, эти раритетные экземпляры никто не хочет покупать. Ну, кроме вас, если вы сюда нажали, увы.", "func", '🧦', "98"],
            '🎣': [2, "монет", "удочка TIER 2","Теперь вы сможете рыбачить не руками с леской и крючком, а с удочкой и леской с крючком!", "func", '🎣', "1575"],
            '♟️': [6, "монет", "пешка", f"Checkmate in {str(random.randint(2, 600))} moves", "func", '♟️', "2009"],
            '🏵️': [1.5, "монет","цветок муосотис", "Прекрасный подарок на любое событие в жизни человека.", "func", '🏵️', "367"],
            '🚘': [8.45, "монет", "собственная тачка","Check out my new гелик!", "func", '🚘', "16650"],
            '🔩': [0.23, "монет", "металлолом декеинг","Очень распространённый материал чтобы использовать его для создания разных штук...", "func", '🔩', "250"],
            '📟': [2.3, "монет", "пейджер","Прямиком из 1980-го года (ну это у нас).", "func", '📟', "487"],
            '🖲️': [2.1, "монет", "красная кнопка", "У-у-у, прямо таки хочется нажать!", "func", '🖲️', "129"],
            '💰': [1, "монет", "мешок с деньгами", "Я посчитал и на это надо гриндить целых 167 часов! Ну, ладно, это если бы шансы рыбы были такими же, но теперь они изменились!", "func", '💰', "5000000"],
            '🧬': [45.3, "монет", "ДНК", "Каким образом это вообще продаётся? Похоже, мы живём в будущем! Я сам определяю свой геном...", "func", '🧬', "999"],
            '🪚': [1.6, "монет", "пилище", "Я бы с такой не играл.", "func", '🪚', "339"],
            '🚪': [1.28, "монет", "дверь", "Дверь мне запили!", "func", '🚪', "199"],
            '🍣': [1.28, "монет", "сашими", "DIY, прямиком из-под ножа!", "func", '🍣', "155"],
            '⛵': [1.12, "монет", "лодка", "преследуешь мечты которые дрим и sail или просто ты лоцман - прямой путь в японию", id26use, '⛵', '2500']
        }

'''
Секция с картами для рыбалки
Формат: Карта, описание, кол-во рыб, координаты hook, координаты лодки, шанс на сокровище, случайные события;
'''

maps = {
    "спокойный океан": [[["◼️", "◼️", "◼️", "◼️", "◼️", "☀️", "◼️"],
                         ["◼️", "◼️", "◼️", "◼️", "◼️", "◼️", "◼️"],
                         ["◼️", "◼️", "◼️", "🛶", "◼️", "◼️", "◼️"],
                         ["🟦", "🟦", "🟦", "🟦", "🟦", "🟦", "🟦"],
                         ["🟦", "🟦", "🟦", "🪝", "🟦", "🟦", "🟦"],
                         ["🟦", "🟦", "🟦", "🟦", "🟦", "🟦", "🟦"],
                         ["🟦", "🟦", "🟦", "🟦", "🟦", "🟦", "🟦"],
                         ["🟦", "🟦", "🟦", "🟦", "🟦", "🟦", "🟦"],
                         ["🟦", "🟦", "🟦", "🟦", "🟦", "🟦", "🟦"],
                         ["🟦", "🟦", "🟦", "🟦", "🟦", "🪸", "🟦"],
                         ["🟨", "🪸", "🟦", "🟦", "🟨", "🟨", "🟨"],
                         ["🟨", "🟨", "🟨", "🟨", "🟨", "🟨", "🟨"]],
                        "Кажется, что именно здесь находятся все тайны этого мира",
                        3,
                        [4, 3],
                        [2, 3],
                        "placeholder",
                        "placeholder"],

    "попасити 2029 год": [[["🟥","🌫","🌫️","🌫","🟥","🟥","🟥","🟥","🟥"],
                  ["🟧","🟧","🟧","🟧","🟧","🟧","🌫","🌫️","🟧"],
                  ["🌆","🌇","🌆","🟧","🛶","🟧","🟧","🟧","🌆"],
                  ["🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦"],
                  ["🟦","🟦","🟦","🟦","🪝","🟦","🟦","🟦","🟦"],
                  ["🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦"],
                  ["🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦"],
                  ["🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦"],
                  ["🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦"],
                  ["🟦","🟫","🟦","🪸","🟦","🟦","🟦","🟦","🟫"],
                  ["🟫","🟫","🟫","🟫","🟦","🟦","⚙️","🟫","🟫"],
                  ["🟫","🟫","🟫","🟫","🟫","🟫","🟫","🟫","🟫"]],
                 "Этот индустриальный город развился до таких масштабов, потому что там не было... сами знаете кого",
                 4,
                 [4, 4],
                 [2, 4],
                 "placeholder",
                 "placeholder"]
}

'''
Команды бота
'''

@client.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def craft(ctx, *, emoji):
    """Команда для крафта различных предметов"""
    crafting_dict = {
        frozenset(['🪚', '🚪', '🔩']): items.get('🎣'),
        frozenset(['🧬', '📟', '🖲️']): items.get('🤖'),
        frozenset(['🎩', '📟', '🖲️']): items.get('🚘'),
        frozenset(['🍌', '♟️', '💩']): items.get('🎩'),
        frozenset(['🐟', '🐠', '🐡']): items.get('🍣'),
        frozenset(['🐟', '🪼', '🐡']): items.get('🍣'),
        frozenset(['🐠', '🪼', '🐡']): items.get('🍣'),
        frozenset(['🐠', '🪼', '🐟']): items.get('🍣'),
        frozenset(['🐟', '🐡']): items.get('🍣'),
        frozenset(['🪼', '🐡']): items.get('🍣'),
        frozenset(['🪼', '🐟']): items.get('🍣'),
        frozenset(['🪼', '🐠']): items.get('🍣'),
        frozenset(['🐡', '🐠']): items.get('🍣'),
        frozenset(['🐟', '🐠']): items.get('🍣'),
        frozenset(['🪚', '🚪', '🚪']): items.get('⛵')

    }

    ingredients = {
        emoji.strip()
        for emoji in emoji.split()
        if emoji.strip() and emoji.strip() != "️"
    }

    found_recipe = None
    for key in crafting_dict:
        if ingredients == key:
            found_recipe = crafting_dict.get(key)
            break
    inventory_data = inventory_ref.child(str(ctx.author.id)).get()

    if inventory_data:

        inventory = []
        inventory_with_timestamps = []

        for key, value in inventory_data.items():
            new_string = re.sub(r'[0-9]', '', key)
            inventory.append(new_string)
            inventory_with_timestamps.append(key)

        items_you_used = []

        if all(item in inventory and not('📌' in item) for item in ingredients):
            for item in ingredients:
                for item2 in inventory_with_timestamps:
                    if item in item2:
                        items_you_used.append(item)
                        inventory_path = f"{str(ctx.author.id)}/{str(item2)}"
                        inventory_ref.child(inventory_path).delete()
                        break

            if found_recipe:
                new_item = inventory_ref.child(str(ctx.author.id)).update(
                    {found_recipe[5] + str(int(time.time() * 1000)): int(int(int(found_recipe[6]) * random.random()) * int(found_recipe[0]))})
                await ctx.send(f"ура, вы скрафтили {found_recipe[5]}")
            else:
                new_item = inventory_ref.child(str(ctx.author.id)).update(
                    {'💩' + str(int(time.time() * 1000)): int(1)})
                await ctx.send(f"ты намудрил с рецептом, и скрафтил {'💩'}.")
        else:

            #new_item = inventory_ref.child(str(ctx.author.id)).update(
            #    {'💩' + str(int(time.time() * 1000)): int(1)})
            await ctx.send(f"у вас не получилось скрафтить предмет.")
            for used_item in items_you_used:
                if used_item in ingredients:
                    if len(ingredients) == 3:
                        await ctx.send(f"возможно, этот предмет используется в крафте: {str(used_item)} + ??? + ???")
                    else:
                        await ctx.send(f"возможно, этот предмет используется в крафте: {str(used_item)} + ???")


    else:
        await ctx.send("ты че как бомжик аид, беги собирать вещи")

@client.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def balance(ctx, member: discord.Member = None):
    """Команда для открытия своего баланса-инвентаря"""
    if member:
        user_data = economy_ref.child(str(member.id)).get()
        user_name = member.display_name
    else:
        user_data = economy_ref.child(str(ctx.author.id)).get()
        user_name = ctx.author.display_name

    karman = user_data['coins']

    if member:
        inventory_data = inventory_ref.child(str(member.id)).get()
    else:
        inventory_data = inventory_ref.child(str(ctx.author.id)).get()



    def balance_sort(page: int, per_page: int = 10):
        #if inventory_data is None:
        #    embed = discord.Embed(title=f'Карман Игрока {user_name}',
        #                          colour=discord.Colour(int('5BC1FF', 16)))
        #    embed.add_field(name='Монетки', value=karman)
        #    return await ctx.send(embed=embed)


        embed = discord.Embed(title=f'Карман Игрока {user_name}', colour=discord.Colour(int('5BC1FF', 16)))
        embed.add_field(name='Монетки', value=karman)



        start = (page - 1) * per_page
        end = start + per_page
        dictlist = []
        for key, value in inventory_data.items():
            temp = (key, value)
            dictlist.append(temp)


        balance_page = dictlist[start:end]
        pattern = r'[0-9]'

        for i, (item_name, quantity) in enumerate(balance_page, start=start + 1):
            new_string = re.sub(pattern, '', item_name)
            if new_string.replace('📌', '') in items:
                multiplier, word, name, way_to_sell, func, icon, price = items.get(new_string.replace('📌', '').strip())
                embed.add_field(name=str(new_string), value=f'{quantity} {word}')
        embed.set_footer(
            text=f"страница {page}/{(len(inventory_data.items()) + per_page - 1) // per_page}"
        )
        return embed

    current_page = 1
    per_page = 12

    embed = balance_sort(current_page, per_page)

    class BalanceView(discord.ui.View):
        def __init__(self, timeout=60):
            super().__init__(timeout=timeout)

        max_pages = (len(inventory_data.items()) + per_page - 1) // per_page

        if max_pages > 1:
            @discord.ui.button(label="Предыдущая страница", style=discord.ButtonStyle.primary)
            async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal current_page
                if current_page > 1:
                    current_page -= 1
                    await interaction.response.edit_message(embed=balance_sort(current_page, per_page), view=self)

            @discord.ui.button(label="Следующая страница", style=discord.ButtonStyle.primary)
            async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                nonlocal current_page
                max_pages = (len(inventory_data.items()) + per_page - 1) // per_page
                if current_page < max_pages:
                    current_page += 1
                    await interaction.response.edit_message(embed=balance_sort(current_page, per_page), view=self)

    await ctx.send(embed = embed, view=BalanceView())
active_games = {}

@client.hybrid_command()
async def sell(ctx, item: str):
    """Команда для продажи вещи/вещей/всего инвентаря"""
    user_id = ctx.author.id
    inventory_data = inventory_ref.child(str(user_id)).get()

    if inventory_data is None:
        await ctx.send('тебе нечего продать на файерградском рынке')

    dictionary = {}
    for item_name, quantity in inventory_data.items():
        dictionary[item_name] = quantity



    what_to_sell = {}
    for item_name, quantity in dictionary.items():
        if item in item_name or item == "inventory":
            if not('📌' in item_name):
                what_to_sell[item_name] = quantity
    print(what_to_sell)
    pattern = r'[0-9]'
    new_string = re.sub(pattern, '', item)

    if len(what_to_sell) >= 1:

        if len(what_to_sell) > 1 and item != "inventory":
            multiplier, word, name, way_to_sell, func, icon, price = items.get(new_string)

            await ctx.send(
                f"ничего себе, у тебя несколько '{item}'. выбери чё продать из этого:\n" +
                "\n".join([f"- {new_string}: {value} {word}" for name, value in what_to_sell.items()])
            )

            msg = await ctx.send('или напиши "всё" если хочешь продать всё сразу')

            def check(m):
                return m.author == ctx.author and m.content.isdigit() and int(m.content) in what_to_sell.values() or m.content == "всё"

        try:
            if len(what_to_sell) > 1 and item != "inventory":
                response = await client.wait_for('message', check=check, timeout=30)

                selected_item = response.content
                if response.content != "всё":
                    await ctx.send(f"окей, ща продадим {item}: {selected_item} {word}")
            else:
                selected_item = "всё"

            funny_copy_what_to_sell = copy.deepcopy(what_to_sell)
            for key, value in what_to_sell.items():
                if str(value) == selected_item or selected_item == "всё":
                    try:
                        inventory_path = f"{user_id}/{key}"
                        inventory_ref.child(inventory_path).delete()
                        user_economy_ref = economy_ref.child(str(user_id))
                        user_data = user_economy_ref.get()

                        if user_data is None:
                            user_economy_ref.set({"coins": 0})

                        if (new_string in key) or (new_string == 'inventory'):
                            if new_string == 'inventory':
                                multiplier, word, name, way_to_sell, func, icon, price = items.get(re.sub(pattern, '', key))
                            else:
                                multiplier, word, name, way_to_sell, func, icon, price = items.get(new_string)

                            sell_price = int(value * multiplier)
                            current_coins = user_data.get("coins", 0)
                            user_economy_ref.update({"coins": current_coins + sell_price})


                            funny_copy_what_to_sell.pop(key)
                            if new_string == 'inventory':

                                cool_string = str(re.sub(pattern, '', key))

                                await ctx.send(f"на файерградском рынке купили {cool_string} за {sell_price} монет")
                            else:
                                await ctx.send(f"на файерградском рынке купили {new_string} за {sell_price} монет")

                        if selected_item != "всё":
                            break
                        elif len(funny_copy_what_to_sell) == 0:
                            break
                    except Exception as e:
                        await ctx.send(f"запор чето не получилось, ошибка {e}")
                else:
                    print("говно переделывай")


            # inventory_ref.child(str(user_id)).child(item)
        except asyncio.TimeoutError:
            await ctx.send("ты чет призадумался, попробуй лучше снова")
    else:
        await ctx.send(f"хрень, такого предмета нету")

@client.command()
@commands.cooldown(3, 1, commands.BucketType.user)
async def use(ctx, *, item: str):
    user_id = ctx.author.id
    inventory_data = inventory_ref.child(str(user_id)).get()

    if inventory_data is None:
        await ctx.send('ты сон у тебя нет предметов')

    dictionary = {}
    for item_name, quantity in inventory_data.items():
        dictionary[item_name] = quantity

    available_items = {}
    for item_name, quantity in dictionary.items():
        if item in item_name or item == "inventory":
            available_items[item_name] = quantity
    pattern = r'[0-9]'
    new_string = re.sub(pattern, '', item)

    multiplier, word, name, description, func, icon, price = items.get(new_string)

    if len(available_items) >= 1:

        if len(available_items) > 1 and item != "inventory":
            await ctx.send(
                f"у тебя несколько '{item}'. выбери конкретный предмет, чтобы использовать предмет \n(скопируй тег вместе с эмодзи или значение после двоеточий):\n" +
                "\n".join([f"- {name}: {value} {word}" for name, value in available_items.items()])
            )

            def check(m):
                return m.author == ctx.author

        try:
            if len(available_items) > 1:
                response = await client.wait_for('message', check=check, timeout=30)

                selected_item = response.content
            else:
                selected_item = item

            try:
                await func(ctx, selected_item)
            except:
                await ctx.send("Этот предмет не имеет никакого применения...")
                return

        except asyncio.TimeoutError:
            await ctx.send("ты чет призадумался, попробуй лучше снова")
    else:
        await ctx.send(f"хрень, такого предмета нету")

@client.command()
@commands.cooldown(1, 1, commands.BucketType.user)
async def pin(ctx, *, item: str):
    pattern = r'[0-9\s]'
    new_item = re.sub(pattern, '', item)
    user_id = ctx.author.id
    inventory_data = inventory_ref.child(str(user_id)).get()

    if inventory_data is None:
        await ctx.send('xnj ты собрался пригвоздить')

    dictionary = {}
    for item_name, quantity in inventory_data.items():
        dictionary[item_name] = quantity


    what_to_pin = {}
    for item_name, quantity in dictionary.items():
        if new_item in item_name or item == "inventory":
            what_to_pin[item_name] = quantity

    new_string = re.sub(pattern, '', new_item)

    multiplier, word, name, way_to_sell, func, icon, price = items.get(new_string.replace('📌', ''))
    if len(what_to_pin) >= 1:

        if len(what_to_pin) > 1 and item != "inventory":

            items_to_pin = []
            for index, (name, value) in enumerate(what_to_pin.items()):
                items_to_pin.append((index, name, value))

            await ctx.send(
                f"выбери, какой из нескольких '{item}' пригвоздить (укажи индекс):\n" +
                "\n".join([f"{index+1}. {new_string}: {value} {word}" for index, name, value in items_to_pin])
            )



            def check(m):
                return m.author == ctx.author and m.content.isdigit()  and 0 <= int(m.content) - 1 < len(items_to_pin) or m.content == "всё"

        try:
            if len(what_to_pin) > 1 and item != "inventory":
                response = await client.wait_for('message', check=check, timeout=30)

                selected_item = response.content
                if response.content != "всё":
                    await ctx.send(f"окей, ща пригвоздим {item}: {value} {word}")
            else:
                selected_item = "всё"

            test_var = None
            funny_copy_what_to_pin = copy.deepcopy(what_to_pin)
            try:
                selected_item = str(int(selected_item)-1)
            except Exception as e:
                pass


            for index, (name, value) in enumerate(what_to_pin.items()):
                if selected_item == str(index) or selected_item == "всё":
                    try:
                        pinorunpin = '📌' in name

                        inventory_path = f"{user_id}/{name}"

                        if new_string in name:
                            funny_copy_what_to_pin.pop(name)
                            if not pinorunpin:
                                inventory_ref.child(inventory_path).delete()
                                inventory_ref.child(str(ctx.author.id)).update({
                                    f'📌{name}': value
                                })
                                await ctx.send(f"вы пригвоздили {new_string}: {value} {word}")
                            else:
                                inventory_ref.child(inventory_path).delete()
                                inventory_ref.child(str(ctx.author.id)).update({
                                    f'{name.replace('📌', '').strip()}': value
                                })
                                await ctx.send(f"вы отгвоздили {new_string}: {value} {word}")

                        if selected_item != "всё":
                            break
                        elif len(funny_copy_what_to_pin) == 0:
                            break
                    except Exception as e:
                        await ctx.send(f"запор чето не получилось, ошибка {e}")

                else:
                    print("говно переделывай")

        except asyncio.TimeoutError:
            await ctx.send("ты чет призадумался, попробуй лучше снова")
    else:
        await ctx.send(f"хрень, такого предмета у тебя нету")


@client.command()
@commands.cooldown(1, 6, commands.BucketType.user)
async def fish(ctx):
    user_id = ctx.author.id
    if user_id in active_games:
        await ctx.send(f"ты уже смешарик, поймай рыбу сначала")
        return

    active_games[user_id] = True
    def double_chance():
        i = 1
        while True:
            if random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 1]):
                i+= 1
            else:
                return i

    class FishGame():

        def __init__(self):
            user_data = economy_ref.child(str(ctx.author.id)).get()
            ref = db.reference(f'inventory/{user_id}/fishing_location')
            try:
                self.word = str(ref.get())
                map_coordinates, description, fish_quantity, hook_coordinates, boat_coordinates, placeholder1, placeholder2 = maps.get(self.word)
            except:
                self.word = "спокойный океан"
                map_coordinates, description, fish_quantity, hook_coordinates, boat_coordinates, placeholder1, placeholder2 = maps.get(self.word)

            self.location_coordinates = copy.deepcopy(map_coordinates)

            self.inventory_data = inventory_ref.child(str(ctx.author.id)).get()

            if user_data is None:
                economy_ref.child(ctx.author.id).set({'coins': 0})


            self.how_many = random.randint(1, fish_quantity)
            self.game_run = True
            self.fish_y = None
            self.fish_x = None
            self.cm = 1
            self.previous_hook = copy.deepcopy(hook_coordinates)
            self.previous_boat = copy.deepcopy(boat_coordinates)


        def rotate_90_clockwise(self):
            ref = db.reference(f'inventory/{user_id}/effects')
            current = ref.get()

            if self.inventory_data is None:
                return
            elif current:
                words = f"{current}".split(";")
                boot_count = words.count("boot")
            else:
                return

            for _ in range(boot_count*2 % 4):
                self.location_coordinates = [list(row) for row in zip(*self.location_coordinates[::-1])]

            for i, row in enumerate(self.location_coordinates):
                if "🪝" in row:
                    j = row.index("🪝")
                    self.previous_hook = [i, j]
                elif "🛶" in row:
                    j = row.index("🛶")
                    self.previous_boat = [i, j]





        def map_print(self):
            self.rotate_90_clockwise()

            # map_one_coordinates, fish_coord = spawn_fish()
            global line
            count = 0
            line = ''
            for row in self.location_coordinates:
                for emoji in row:
                    if count < len(self.location_coordinates[0]):

                        line = line + f''.join(emoji)
                        count += 1
                    else:
                        line = line + f''.join('\n')
                        line = line + f''.join(emoji)
                        count = 1
            return line

        def move_boat(self, x, y, new_x):
            global raw_map

            raw_map = self.location_coordinates
            what_to_change = self.location_coordinates[y][x+new_x]
            raw_map[y][x + new_x] = "🛶"
            raw_map[y][x] = what_to_change
            self.previous_boat[1] += new_x
            return raw_map



        def spawn_fish(self):

            choice_x = [0, 6]
            choice_y = [5, 8]
            inventory_data = inventory_ref.child(str(ctx.author.id)).get()

            fish_available = {
                'спокойный океан': [['🐟', '🐟', '🐟', '🐟', '🐟', '🐠', '🐠', '🐠', '🐡', '🪼', '👢'], ['🐟','🐟','🐟', '🐟', '🐟', '🐠', '🐠', '🐠', '🐡', '🪼', '👢', '🦐', '🦐', '🐙', '🦈', '🐚', '🐚']],
                'попасити 2029 год': [['🚪'] * 30 + ['🔩'] * 20 + ['📟'] + ['🖲️'] + ['💩'] * 5 + ['👢'] * 5, ['🚪'] * 20 + ['🔩'] * 15 + ['📟'] * 3 + ['🖲️'] * 2 + ['💩'] * 1 + ['👢'] * 1]
            }

            no_fish_rod, level1_fish_rod = fish_available.get(self.word)

            fish_emojis = no_fish_rod

            if inventory_data is None:
                pass
            else:
                fish_rod_list = []
                for key, value in inventory_data.items():
                    new_string = re.sub(r'[0-9]', '', key)
                    fish_rod_list.append(new_string)

                if ('🎣' in fish_rod_list) or ('📌🎣' in fish_rod_list):
                    fish_emojis = level1_fish_rod

            # fish_emojis = ['👢']



            global raw_map
            raw_map = self.location_coordinates
            self.fish_y = random.choice(choice_y)
            self.fish_x = random.choice(choice_x)
            fish_coords = [self.fish_y, self.fish_x]
            raw_map[self.fish_y][self.fish_x] = random.choice(fish_emojis)


            return raw_map, fish_coords



        def change_coord(self, x, y, new_x, new_y):
            # if previous_hook[0] > 3 or new_y == -1:
            # global game_run

            CATCH_LIST = ['🐟','🐠', '🐡','🪼', '🦐', '🦈', '👢', '🐚', '🚪', '🔩', '📟', '🖲️', '💩']

            global raw_map
            what_to_change = self.location_coordinates[y+new_y][x+new_x]
            if (what_to_change != "🟨") and (what_to_change != "🪸") and (what_to_change != "◼️") and (what_to_change != "🛶") and (what_to_change != "🟫") and (what_to_change != "🟧") and (what_to_change != "🌆") and (what_to_change != "🌇") and (what_to_change != "⚙️") and (not (what_to_change in CATCH_LIST)):
                raw_map = self.move_boat(self.previous_boat[1], self.previous_boat[0], new_x)
                # raw_map = map_one_coordinates
                raw_map[y+new_y][x+new_x] = "🪝"
                raw_map[y][x] = what_to_change
                self.previous_hook[0] += new_y
                self.previous_hook[1] += new_x
                global line
                count = 0
                line = ''
                for row in raw_map:
                    for emoji in row:
                        if count < len(self.location_coordinates[0]):

                            line = line + f''.join(emoji)
                            count += 1
                        else:
                            line = line + f''.join('\n')
                            line = line + f''.join(emoji)
                            count = 1
                return line
            else:
                inventory_data = inventory_ref.child(str(ctx.author.id)).get()
                if inventory_data is None:
                    pass
                else:
                    fish_rod_list = []
                    for key, value in inventory_data.items():
                        fish_rod_list.append(key)
                    if ('🎣' in fish_rod_list) or ('📌🎣' in fish_rod_list):
                        self.cm = random.randint(1, 200) * (double_chance())
                    else:
                        self.cm = random.randint(1, 100) * (double_chance())

                fish_book = {
                    '🐟': [f"вы поймали карася размером {self.cm} сантиметров", 1, "fish"],
                    '🐠': [f'вы поймали брата карася размером {self.cm} сантиметров', 1, "fish"],
                    '🐡': [f'вы поймали рыбу агу ага размером {self.cm} сантиметров', 1, "fish"],
                    '🪼': [f'вы поймали медузу крутую размером {self.cm} сантиметров', 1, "fish"],
                    '🦐': [f'вы поймали креветочку размером {self.cm} сантиметров', 1, "fish"],
                    '🦈': [f'Трепещи, rer_5111, я поймать АКУЛУ размером {self.cm} сантиметров!', 1, "fish"],
                    '👢': [f'вы поймали грязный ботинок из австралии.', random.randint(1, 10), "item"],
                    '🐚': [f'вы поймали плавающую ракушку.', random.randint(10, 30), "item"],
                    '🚪': [f'вы поймали Д.В.Е.Р.Ь.', random.randint(10, 300), "item"],
                    '🔩': [f"вы поймали болт фром тхандер (на самом деле металлолом...)", random.randint(1, 100),
                          "item"],
                    '📟': [f"вы поймали что это нахер", random.randint(100, 500), "item"],
                    '🖲️': [f"вы поймали жми на кнопку, кронк", random.randint(50, 200), "item"],
                    '💩': [f"фу чё это так воняет, убери этот навоз", 1, "item"]

                }

                if what_to_change in fish_book.keys():
                    line, multiplier, typeof = fish_book.get(what_to_change)
                    inventory_data = inventory_ref.child(str(ctx.author.id)).get()

                    if inventory_data is None:
                        if typeof == "fish":
                            inventory_ref.child(str(ctx.author.id)).set({what_to_change + str(int(time.time() * 1000)): self.cm * multiplier})
                        else:
                            inventory_ref.child(str(ctx.author.id)).set({what_to_change + str(int(time.time() * 1000)): 1 * multiplier})
                    else:
                        if typeof == "fish":
                            current_fish = inventory_ref.child(str(ctx.author.id)).update({
                                what_to_change + str(int(time.time() * 1000)): self.cm * multiplier
                            })
                        else:
                            current_fish = inventory_ref.child(str(ctx.author.id)).update({
                                what_to_change + str(int(time.time() * 1000)): 1 * multiplier
                            })

                    game_run = False
                    active_games.pop(user_id, None)
                    return line

                count = 0
                line = ''
                for row in raw_map:
                    for emoji in row:
                        if count < len(self.location_coordinates[0]):
                            line = line + f''.join(emoji)
                            count += 1
                        else:
                            line = line + f''.join('\n')
                            line = line + f''.join(emoji)
                            count = 1
                return line

    game_up = FishGame()



    class Buttons(discord.ui.View):
        def __init__(self, author, timeout=None):
            super().__init__(timeout=timeout)
            self.author = author

        for i in range(game_up.how_many):
            game_up.spawn_fish()

        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji='⬆️')
        async def up(self, interaction: discord.Interaction, button: discord.ui.Button):

            desc = game_up.change_coord(game_up.previous_hook[1], game_up.previous_hook[0], 0, -1)
            new_embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)), title=f'фишинг {ctx.author.display_name}', description=desc)
            if "🟦" in new_embed.description:
                await message.edit(embed=new_embed, view=Buttons(ctx.author, timeout=None))
            else:
                await message.edit(embed=new_embed, view=None)
            await interaction.response.defer()

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji='⬇️')
        async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
            desc = game_up.change_coord(game_up.previous_hook[1], game_up.previous_hook[0], 0, 1)
            new_embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)), title=f'фишинг {ctx.author.display_name}', description=desc)
            if "🟦" in new_embed.description:
                await message.edit(embed=new_embed, view=Buttons(ctx.author, timeout=None))

            else:
                await message.edit(embed=new_embed, view=None)
            await interaction.response.defer()

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji='⬅️')
        async def left(self, interaction: discord.Interaction, button: discord.ui.Button):
            desc = game_up.change_coord(game_up.previous_hook[1], game_up.previous_hook[0], -1, 0)
            new_embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)),
                                      title=f'фишинг {ctx.author.display_name}', description=desc)
            if "🟦" in new_embed.description:
                await message.edit(embed=new_embed, view=Buttons(ctx.author, timeout=None))
            else:
                await message.edit(embed=new_embed, view=None)
            await interaction.response.defer()


        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji='➡️')
        async def right(self, interaction: discord.Interaction, button: discord.ui.Button):
            desc = game_up.change_coord(game_up.previous_hook[1], game_up.previous_hook[0], 1, 0)
            new_embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)),
                                      title=f'фишинг {ctx.author.display_name}', description=desc)
            if "🟦" in new_embed.description:
                await message.edit(embed=new_embed, view=Buttons(ctx.author, timeout=None))
            else:
                await message.edit(embed=new_embed, view=None)
            await interaction.response.defer()

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id


    embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)), title=f'фишинг {ctx.author.display_name}', description=game_up.map_print())
    if "вы" in embed.description:
        message = await ctx.send(embed=embed, view=None)
        await message.edit(embed=embed, view=None)
    else:
        message = await ctx.send(embed=embed, view=Buttons(ctx.author, timeout=None))

    while game_up.game_run:
        await asyncio.sleep(1)

    print(active_games)
# d

ITEMS = [
    { "name": ""}

]


def parse_time(time_str: str) -> int:
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    match = re.fullmatch(r"(\d+)([smhd])", time_str.lower())
    if not match:
        raise ValueError("какашно вводишь время")
    value, unit = match.groups()
    if int(value) < 99999:
        return int(value) * time_units[unit]
    else:
        raise ValueError("какашно вводишь время")

@client.hybrid_command(name = "клетка", with_app_command = True)
@app_commands.describe(member="юзер", time="время (s/m/h/d)")
@commands.has_permissions(administrator = True)
async def клетка(ctx: commands.Context, member: discord.Member, time: str, bananas: str = None, *, reason: str = None):
    try:
        role_id = servers_ref.child(str(ctx.guild.id)).get().get("TIMEOUT_ROLE_ID")
        role = ctx.guild.get_role(int(role_id))
    except:
        role = None

    if role is None:
        message = await ctx.send(
            "какой же всё таки пипец что бот не настроен... админы напишите `/settings` и добавьте TIMEOUT_ROLE_ID (роль, которая даётся пользователям для таймаута)")
        return

    saved_roles = member.roles
    if reason is not None:
        if len(reason) > 1024:
            await ctx.reply("что биографию свою пишешь чтоли")
            return



    try:
        if not (bananas is None):
            new_bananas = int(bananas)
            if new_bananas <= 0 or new_bananas > 99999:
                raise ValueError("емае ну и хрень они пишут")
        else:
            pass

    except ValueError as e:
        await ctx.reply(f"что за бред с бананами: {e}")
        return
    if role in member.roles:
        await ctx.reply(f"{member.mention} уже там", ephemeral=True)
        return
    try:
        time_in_seconds = parse_time(time)
        if time_in_seconds <= 0:
            raise ValueError("еперный театр")
    except ValueError as e:
        await ctx.reply("какашечно вводишь время")
        return

    server_dict = servers_ref.child(str(ctx.guild.id)).get()
    try:
        channel = client.get_channel(int(server_dict.get("TIMEOUT_CHANNEL_ID")))
    except:
        channel = None

    if not channel:
        message = await ctx.send(
            "какой же всё таки пипец что бот не настроен... админы напишите `/settings` и добавьте TIMEOUT_CHANNEL_ID (канал для таймаутов)")
        return

    try:
        await member.add_roles(role)
        try:
            # await member.remove_roles(players)
            # await member.remove_roles(unplayers)
            pass
        except:
            pass

        await ctx.reply(f"отправляется в орангутан {member.mention}.")

        # number_of_things = random.randint(500, 1000)
        if bananas:
            number_of_things = bananas

        names = ["бананов"]
        things = ["🍌"]
        thing = random.choice(things)
        name = names[things.index(thing)]

        if bananas:
            user_penalty = penalty_ref.child(str(member.id)).get()

            if user_penalty is None:
                penalty_ref.child(str(member.id)).set({'penalty': int(bananas)})
            else:
                penalty_ref.child(str(member.id)).update({'penalty': int(bananas)})

        if channel:
            embed = discord.Embed(
                title = f"добро пожаловать в этот канал, {member}",
                description = f"вы очевидно в чём-то провинились раз здесь оказались.",
                color = discord.Color.blurple()
            )
            now = datetime.now()
            end_time = now + timedelta(seconds=time_in_seconds)
            unix_timestamp = int(end_time.timestamp())


            embed.add_field(name="Вы будете находиться здесь до:", value=f"<t:{unix_timestamp}>")

            if reason:
                embed.add_field(name="здесь осталась записка. вот, кстати, её текст:", value=f"{reason}", inline=False)
                embed.add_field(name="автор:", value=f"-{ctx.author}")


            if bananas:
                embed.add_field(name=f"Чтобы выбраться отсюда, вам необходимо:", value=f"почистить {number_of_things} {name}, используя !почистить {thing}", inline=False)
            await channel.send(embed=embed)
        else:
            message = await ctx.send(
                "кто удалил канал")
            return

        await asyncio.sleep(time_in_seconds)
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"ёмаё, {member.mention} выпустили из обезяника")
            penalty_ref.child(str(member.id)).delete()

    except Exception as e:
        await ctx.reply(f"ну что за понос: {e}")


cool_dict = {}


async def get_user(user_cool_id):
    if not user_cool_id in cool_dict:
        try:
            user = await client.fetch_user(int(user_cool_id))
            cool_dict[user_cool_id] = user.display_name
        except discord.NotFound:
            cool_dict[user_cool_id] = user_cool_id
    return cool_dict[user_cool_id]


@client.hybrid_command(name = "info", with_app_command = True)
async def info(ctx, *, item: str):
    user_id = ctx.author.id
    inventory_data = inventory_ref.child(str(user_id)).get()

    if inventory_data is None:
        await ctx.send('xnj ты информацию ищешь в космосе (пантигон привет)')

    dictionary = {}
    for item_name, quantity in inventory_data.items():
        dictionary[item_name] = quantity


    available_items = {}
    for item_name, quantity in dictionary.items():
        if item in item_name or item == "inventory":
            available_items[item_name] = quantity
    pattern = r'[0-9]'
    new_string = re.sub(pattern, '', item)

    multiplier, word, name, description, func, icon, price = items.get(new_string)

    if len(available_items) >= 1:

        if len(available_items) > 1 and item != "inventory":
            await ctx.send(
                f"у тебя несколько '{item}'. выбери конкретный предмет, чтобы посмотреть информацию о нём\n(скопируй тег вместе с эмодзи или значение после двоеточий):\n" +
                "\n".join([f"- {name}: {value} {word}" for name, value in available_items.items()])
            )

            def check(m):
                return m.author == ctx.author

        try:
            if len(available_items) > 1:
                response = await client.wait_for('message', check=check, timeout=30)

                selected_item = response.content
            else:
                selected_item = new_string


            for key, value in available_items.items():
                if str(value) == selected_item or str(key) == selected_item or len(available_items) == 1:
                    cleaned_text = re.sub(r'^[^\d]*', '', key)

                    embed = discord.Embed(title=f'Карман Игрока {ctx.author.display_name}', colour=discord.Colour(int('5BC1FF', 16)))
                    embed.add_field(name=new_string, value=f"{name}, предмет получен <t:{str(int(cleaned_text)//1000)}:F>")
                    embed.add_field(name="Описание:", value=description)
                    await ctx.send(embed=embed)



        except asyncio.TimeoutError:
            await ctx.send("ты чет призадумался, попробуй лучше снова")
    else:
        await ctx.send(f"хрень, такого предмета нету")


@client.hybrid_command(name = "leaderboard", with_app_command = True)
async def leaderboard(ctx):
    if ctx.interaction:
        await ctx.interaction.response.defer()
    users_data = economy_ref.get()
    specific_user_data = {f"{await ctx.guild.fetch_member(member.id)}": member.id for member in
                          ctx.guild.members}

    users = {}
    for user_id, money in users_data.items():
        user_cool_id = await get_user(user_id)
        users[user_cool_id] = int(money.get("coins"))

    def find_money(cool_user_id):
        return economy_ref.child(str(cool_user_id)).get()

    def get_sorted():
        if int(is_global) == 1:
            return sorted(users.items(), key=lambda x: x[1], reverse=True)
        else:
            coins_data = {}
            for nickname, specific_user_id in specific_user_data.items():
                try:
                    coins_dict = find_money(specific_user_id)
                    coins = int(coins_dict.get('coins'))
                    if coins_dict is not None:
                        coins_data[nickname] = coins
                    else:
                        pass
                except:
                    pass
            return sorted(coins_data.items(), key=lambda x: x[1], reverse=True)

    def get_leaderboard_page(page: int, per_page: int = 10):

        sorted_data = get_sorted()
        start = (page - 1) * per_page
        end = start + per_page
        leaderboard_page = sorted_data[start:end]


        embed = discord.Embed(
            title="Великий Лидерборд",
            description= "вот они слева направо:",
            color=discord.Color.dark_gold()
        )
        for i, (name, score) in enumerate(leaderboard_page, start=start + 1):
            embed.add_field(name=f"{i}. {name}", value=f"{score} монеток", inline=False)
        embed.set_footer(
            text=f"страница {page}/{(len(sorted_data) + per_page - 1) // per_page}"
        )
        return embed

    current_page = 1
    per_page = 10

    # embed = get_leaderboard_page(current_page, per_page)
    class ServerSelectView(discord.ui.View):
        def __init__(self, author_id: int, timeout=60):
            super().__init__(timeout=timeout)
            self.author_id = author_id
            self.servers = list(client.guilds)
            menu = Select(
                placeholder="Выберите тип Лидерборда",  # Текст по умолчанию
                options=[
                    discord.SelectOption(
                        label="Локальный Лидерборд",
                        value="0",
                        description="Показывает лидерборд текущего сервера"
                    ),
                    discord.SelectOption(
                        label="Глобальный Лидерборд",
                        value="1",
                        description="Показывает лидерборд со всех серверов"
                    ),
                ]
            )

            menu.callback = self.on_select
            self.add_item(menu)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user.id != self.author_id:
                return False
            return True

        async def on_select(self, interaction: discord.Interaction):
            await interaction.response.defer()
            global is_global
            is_global = interaction.data["values"][0]

            await interaction.edit_original_response(embed=get_leaderboard_page(current_page, per_page),
                                                         view=LeaderboardView())

    class LeaderboardView(discord.ui.View):
        def __init__(self, timeout=60):
            super().__init__(timeout=timeout)

        @discord.ui.button(label="Предыдущая страница", style=discord.ButtonStyle.primary)
        async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            nonlocal current_page
            if current_page > 1:
                current_page -= 1
                await interaction.response.edit_message(embed=get_leaderboard_page(current_page, per_page), view=self)

        @discord.ui.button(label="Следующая страница", style=discord.ButtonStyle.primary)
        async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            nonlocal current_page
            max_pages = (len(get_sorted()) + per_page - 1) // per_page
            if current_page < max_pages:
                current_page += 1
                await interaction.response.edit_message(embed=get_leaderboard_page(current_page, per_page), view=self)

    await ctx.send(view=ServerSelectView(author_id=ctx.author.id))

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def почистить(ctx, emoji):
    try:
        timeout_role_id = servers_ref.child(str(ctx.guild.id)).get().get("TIMEOUT_ROLE_ID")
    except:
        await ctx.send("увы даже такой роли нету... пусть админ напишет `/settings` и настроит TIMEOUT_ROLE_ID")
        return

    if not timeout_role_id or not any(role.id == int(timeout_role_id) for role in ctx.author.roles):
        await ctx.send("ты норм, иди отдыхай")
        return

    inventory_data = economy_ref.get()
    cool_list = []
    for id, inventory in inventory_data.items():
        pass
        cool_list.append(str(id))

    cool_list.remove(str(ctx.author.id))

    user_id = random.choice(cool_list)

    penalty_data = penalty_ref.child(str(ctx.author.id)).get()
    current_penalty = int(penalty_data.get("penalty"))
    if current_penalty:
        if cool_list:
            if emoji == "🍌":
                user_data = inventory_ref.child(user_id).get()
                if user_data is None:
                    inventory_ref.child(user_id).set({'🍌' + str(int(time.time() * 1000)): 1})
                else:
                    new_banana = inventory_ref.child(user_id).update({
                        '🍌' + str(int(time.time() * 1000)): 1
                    })

                if current_penalty > 0:
                    new_penalty = max(0, current_penalty - 1)
                    penalty_ref.child(str(ctx.author.id)).update({"penalty": new_penalty})

                    await ctx.reply(f"вы почистили 🍌, осталось {new_penalty}")

                    if new_penalty == 0:
                        guild = ctx.guild
                        member = guild.get_member(int(ctx.author.id))
                        try:
                            target_role = ctx.guild.get_role(int(timeout_role_id))
                        except:
                            target_role = None

                        if member:
                            if target_role in member.roles:
                                await member.remove_roles(target_role)
                                penalty_ref.child(str(ctx.author.id)).delete()
                                await ctx.send(f"ёмаё, {member.mention} выпустили из обезяника")
    else:
        await ctx.reply("да нельзя щас")

async def shop_Changed(ctx: discord.ext.commands.Context, msg: discord.Message):
    pass

class ShopClass():
    def __init__(self):
        self.embed = discord.Embed(color=Color.dark_purple(), title="Магазин", description=None)

        self.chosen_keys = []


    def initialize_shop(self):
        self.embed = discord.Embed(color=Color.dark_purple(), title="Магазин", description=None)
        self.chosen_keys = []
        shop_catalogue = list(items.values())
        for _ in range(3):
            self.chosen_keys.append(random.choice(shop_catalogue))

        for i in self.chosen_keys:

            if self.chosen_keys.count(i) > 1:
                save_index = i
                while self.chosen_keys.count(save_index) != 1:
                    self.chosen_keys.remove(save_index)
                    self.chosen_keys.insert(self.chosen_keys.index(save_index),random.choice(shop_catalogue))

        for item in self.chosen_keys:
            self.embed.add_field(name=item[5], value=item[2], inline=True)
            self.embed.add_field(name=f"{item[6]}", value="\n", inline=False)


        return self.chosen_keys

    def shop_view(self):
        self.embed = discord.Embed(color=Color.dark_purple(), title="Магазин", description=None)
        for item in self.chosen_keys:
            self.embed.add_field(name=item[5], value=item[2], inline=True)
            self.embed.add_field(name=f"{item[6]}", value="\n", inline=False)
        return self.embed

myshop = ShopClass()
# shop_items = initialize_shop()

@client.hybrid_command()
async def meme(ctx):
    links = ['https://tenor.com/view/%D1%86%D0%B2%D0%B5%D1%82%D1%8B-%D1%87%D0%B0%D0%B9-gif-402293663251947105','https://medal.tv/ru/games/minecraft/clips/jJYaWupK5FPvcuyIA?invite=cr-MSxtdEcsMTQxNjg3NzEzLA','https://medal.tv/ru/games/minecraft/clips/jJY835WlKTgizxlQ9?invite=cr-MSxxblIsMTQxNjg3NzEzLA', 'https://medal.tv/ru/games/minecraft/clips/jJY70nnSokD8toCJ9?invite=cr-MSxIcGwsMTQxNjg3NzEzLA', 'https://tenor.com/view/cat-vro-mei-mei-mei-tole-tole-gif-12564264859640410840', 'https://tenor.com/view/cat-brain-cat-brain-ice-cream-gif-25160275', 'https://medal.tv/ru/games/roblox/clips/jFznrb3IsHB56g54M?invite=cr-MSw1T0QsMTQxNjg3NzEzLA', 'https://www.twitch.tv/mrtomit/clip/GorgeousPoisedAlfalfaTakeNRG-eLgJor8iJtWB3QZF', 'https://www.twitch.tv/mrtomit/clip/FitEasyKeyboardCoolStoryBob-2Gsd_aYYD9jpGtUg', 'https://www.twitch.tv/mrtomit/clip/IntelligentRelentlessCurlewBrainSlug-s0wWdky0tqSnkQrj', 'https://medal.tv/ru/games/minecraft/clips/jwnWpNg7UDR-3-iHv?invite=cr-MSxTU08sMTQxNjg3NzEzLA', 'https://tenor.com/view/mee6-gif-24405001', 'https://media.discordapp.net/attachments/1051934380924338186/1070396001069830164/tomatloh.gif?ex=67cc7ef5&is=67cb2d75&hm=02f587046e1bc2b06d110ad1fe94fceb59a4838feea657a69ac233346a158424&', 'https://cdn.discordapp.com/attachments/1042878735965245512/1215755642887733279/caption_2.gif?ex=67cca62c&is=67cb54ac&hm=e30478da92d22cc414b63636b6c64b84296192b2262c5aa6406487763972a9ad&', 'https://tenor.com/view/mod-purge-discord-mods-i-hate-this-server-moderation-team-mods-gif-25676559', 'https://medal.tv/ru/games/roblox/clips/jshIdvtCYSb63cNCX?invite=cr-MSx6V3MsMTQxNjg3NzEzLA', 'https://medal.tv/ru/games/roblox/clips/jsfwZDchKGDMHnHpD?invite=cr-MSxOWm4sMTQxNjg3NzEzLA', 'https://media.discordapp.net/attachments/514133658529955860/1090354788757151985/caption.gif?ex=67cc9887&is=67cb4707&hm=53bbfc5df69be22d5ea11a447da353860b731d5afec923aa9dcc67fd984ac537&', 'https://cdn.discordapp.com/attachments/514133658529955860/1325466408846495764/caption.gif?ex=67ccf889&is=67cba709&hm=ff1f197744a3238fc00a0def19bdf6ccf6610bfa206d6740ca7bdf09da1267fd&', 'https://cdn.discordapp.com/attachments/514133658529955860/1260302509122129992/caption.gif?ex=67cc8d2d&is=67cb3bad&hm=b7c54bbd078100cfcf18d9aeaa5fc1bd11624341d3c9c7057ff3b8253dfc8359&', 'https://media.discordapp.net/attachments/553533944063328258/998448833384165436/gif_1.gif?ex=67cc72b0&is=67cb2130&hm=99e69ccb13faf0ae5fad122b1a3699110abdc1b39c9efade2119098ce1a0bda0&', 'https://medal.tv/ru/games/minecraft/clips/jn2XHhdUnLvMgvVRu?invite=cr-MSxpT04sMTQxNjg3NzEzLA', 'https://tenor.com/view/whatsapp-gif-21302024', 'https://medal.tv/ru/games/roblox/clips/ji1m01PfySaoovvHf?invite=cr-MSw2VjYsMTQxNjg3NzEzLA', 'https://medal.tv/ru/games/roblox/clips/jhYcunAnPzurVIq1S?invite=cr-MSw0SW0sMTQxNjg3NzEzLA', 'https://medal.tv/ru/games/roblox/clips/ji6rLVePCEVKLLn9F?invite=cr-MSxJa1UsMTQxNjg3NzEzLA', 'https://medal.tv/ru/games/roblox/clips/ji2bjrYZVCBQFL-5n?invite=cr-MSxLRFAsMTQxNjg3NzEzLA', 'https://tenor.com/view/dr-nefario-fart-gun-gif-20054143', 'https://www.twitch.tv/mrtomit/clip/MushyMuddyAnteaterDuDudu-aSMzoKsrMGojjo2J',
             'https://www.twitch.tv/mrtomit/clip/OilyDullAyeayeRuleFive-HBvwpd_nYK4AYR0C', 'https://www.twitch.tv/mrtomit/clip/EnthusiasticAntediluvianBeaverHoneyBadger-I8yyRPltC69tuDbE', 'https://www.twitch.tv/mrtomit/clip/MoralHonorableInternRalpherZ-_-PUox4KXRgWwGJU', 'https://www.twitch.tv/mrtomit/clip/BoringZealousBeefWoofer-VOXHq9cxRk9YUSKS', 'https://tenor.com/view/average-conversation-in-this-server-discord-server-donowall-ignored-gif-2054677438560113125', 'https://tenor.com/view/alexs-caves-orb-primordial-caves-puss-in-boots-jack-horner-gif-27498505', 'https://medal.tv/ru/games/minecraft/clips/j41c7aexClFC6nwd8?invite=cr-MSxvZHUsMTQxNjg3NzEzLA', 'https://tenor.com/view/adequate-rules-say-it-and-u%27ll-be-muted-gif-701907492395044116', 'https://medal.tv/ru/games/buckshot-roulette/clips/j2poCpkE5nGqNIQ_k?invite=cr-MSxreTQsMTQxNjg3NzEzLA', 'https://www.youtube.com/watch?v=WAkQKVdP9Eo', 'https://tenor.com/view/green-alien-cat-green-alien-green-cat-alien-gif-721538137659195618', 'https://tenor.com/view/not-a-sigma-sorry-you-are-not-a-sigma-sorry-you%27re-not-a-sigma-you-aren%27t-a-sigma-you-are-not-sigma-gif-337838532227751572', 'https://tenor.com/view/mystical-wise-tree-a-little-goofy-omg-rofl-lmfao-gif-3707288582733751132', 'https://tenor.com/view/da-gif-10183464272850732800', 'https://cdn.discordapp.com/emojis/1098375901248487424.gif?size=48&quality=lossless&name=tomatjret', 'https://tenor.com/view/cat-funny-cat-funny-smile-happy-gif-7621419476068285580', 'https://www.twitch.tv/mrtomit/clip/ClumsyFriendlyPeafowlCharlietheUnicorn-p1_hf_ZmOHxCNlwi', 'https://www.twitch.tv/mrtomit/clip/CoweringSingleTruffleTwitchRPG-anHX7unyQd5QpHAw', 'https://www.twitch.tv/mrtomit/clip/CuriousLittleCheddarPoooound-kaGI74ieAMs3h2dS', 'https://www.twitch.tv/mrtomit/clip/FragileQuaintDotterelAllenHuhu-ZHdHk8J8Usu4E-NN', 'https://www.twitch.tv/mrtomit/clip/ClumsyCarelessTermiteWutFace-d5lVNrbrD4pacThE',
             'https://www.twitch.tv/mrtomit/clip/InnocentTallStapleTooSpicy-7U3mOB4tq37igmMg', 'https://www.twitch.tv/mrtomit/clip/ExpensiveInexpensiveMangoAsianGlow-hykemhVcqOOP5rCx', 'https://www.twitch.tv/mrtomit/clip/PoliteEagerGiraffeNotATK-6o5MjFttmdgJ2_Kc', 'https://www.twitch.tv/mrtomit/clip/PolishedTalentedTaroSmoocherZ-dw3ZOPk-5J32SNP7', 'https://www.twitch.tv/mrtomit/clip/TolerantGrotesqueKeyboardTooSpicy-7XPV1rjaHx-RtNVQ', 'https://www.twitch.tv/mrtomit/clip/SuperWealthyDurianFutureMan-9BROPxcADpqQS77P', 'https://www.twitch.tv/mrtomit/clip/ToughExuberantSproutCharlietheUnicorn-LnEiuLOHGKQswvjv', 'https://www.twitch.tv/mrtomit/clip/DifferentWealthyMageTheRinger-68uh9EOGPr6UNYjg', 'https://cdn.discordapp.com/attachments/514133658529955860/1273741999169605752/caption.gif?ex=67ccaa2d&is=67cb58ad&hm=8a5596ec48454bae1c7e4c2922a197714f3dacf6a62ce68ac3dcea65132d6596&', 'https://tenor.com/view/discord-reaction-gif-23868418', 'https://youtu.be/zX2SjdImGc8?si=Xysr-TubGIEkMZXm', 'https://clips.twitch.tv/SpinelessBumblingChickenItsBoshyTime-IrCDa27GBWoUEWOa', 'https://clips.twitch.tv/MoralTallNigiriFloof-sd9EXhBPQECize_k', 'https://cdn.discordapp.com/emojis/1252846764206329906.webp?size=48&quality=lossless&name=smartass', 'https://media.discordapp.net/attachments/694981054406066319/1065255144247271524/caption.gif?ex=67cce8e9&is=67cb9769&hm=bef0e13b79e9a07455ed34128134e35cb5cd5c7ea40d13d44f30897833b1ec1a&', 'https://tenor.com/view/cat-uncanny-cat-canny-cat-uncanny-canny-gif-2341506220249338090', 'https://tenor.com/view/minecraft-create-mod-technology-gif-25752533', 'https://tenor.com/view/podolsk-gif-20371232', 'https://tenor.com/view/roblox-roblox-meme-roblox-obby-roblox-jumpscare-gif-25132757', 'https://tenor.com/view/tushmar-snail-eating-tomato-funny-epic-gif-tushmar-tier3overwatch-coach-tier3overwatch-gif-20907469', 'https://tenor.com/view/spinning-tomato-gif-24526359', 'https://clips.twitch.tv/GlutenFreeHyperShrimpKlappa-WQLHquJBYOdoFGOj', 'https://clips.twitch.tv/CrypticVenomousLlamaBabyRage-l170WlMC13AqjK0F', 'https://clips.twitch.tv/GoldenShakingDotterelPartyTime-gZufXanWjjBql55J', 'https://clips.twitch.tv/ResourcefulConfidentSwallowPJSugar-qc0CU_MHYJszcgBU', 'https://clips.twitch.tv/LittleSilkySnailTheThing-omXZQ7CTuwohHy6Y', 'https://tenor.com/view/minecraft-create-aerodynamics-strike-gif-25269807', 'https://tenor.com/view/%D0%B0-4-gif-14211769093273171637', 'https://cdn.discordapp.com/attachments/305834181949390848/524302853087428618/Screenshot_2018-12-06-15-58-35.png?ex=67cc9695&is=67cb4515&hm=225057b60d58a33494f5d6bd4ce446ba4355fb9dd57316bc0f60b0355f764d09&uc=dp&', 'https://tenor.com/view/%E0%B8%95%E0%B8%B2%E0%B8%A2%E0%B9%81%E0%B8%9E%E0%B8%A3%E0%B9%8A%E0%B8%9A-cpr-revive-cat-gif-15837553', 'https://tenor.com/view/bogo-moment-bogo-sort-sorting-bogo-sort-moment-bogo-gif-25634188', 'https://tenor.com/view/hey-all-scott-here-this-gif-27154582', 'https://tenor.com/view/death-corridor-death-corridor-geometry-dash-geometry-gif-15673481441265769442', 'https://tenor.com/view/funny-spongebob-gif-17598597586521616942', 'https://clips.twitch.tv/GiftedRockySquidVoteNay-ny2FT1oBAobYJhuP', 'https://clips.twitch.tv/EnthusiasticEsteemedPidgeonOMGScoots-FI5RTCSWmXaNsR_0', 'https://clips.twitch.tv/DeadRespectfulLocustYee-eHifj9sUYoLAR7hu', 'https://clips.twitch.tv/CredulousSpotlessPorcupineSaltBae-ddzQ_lrackVQZe5-', 'https://clips.twitch.tv/BloodyAlivePhoneWutFace-sdCrtJ0-I8WRM9au', 'https://clips.twitch.tv/ManlyIgnorantChamoisKappaClaus-GmtQ4yhMTOVYJw_3', 'https://clips.twitch.tv/FurryHotTofuHassanChop-wN_AwzhC9BCFDDMk', 'https://clips.twitch.tv/JoyousElegantPeppermintOptimizePrime-Oj00JndiXcgSzd78', 'https://clips.twitch.tv/CallousGorgeousMageAliens-ru8Not0PreO5nNVx', 'https://tenor.com/view/cat-power-cat-cat-pillow-repost-this-post-this-cat-gif-23865940', 'https://tenor.com/view/frog-frog-laughing-gif-25708743',
             'https://clips.twitch.tv/SincereBoredStarBuddhaBar-Q4W-e2OpENBN7ynD', 'https://tenor.com/view/taeuvre-squidward-squidward-shocked-squidward-break-gif-26165410', 'https://tenor.com/view/cringe-death-dies-of-cringe-davy-jones-dying-of-cringe-gif-22207406', 'https://tenor.com/view/troll-trolled-trollge-troll-success-gif-22597471', 'https://media.discordapp.net/attachments/514133658529955860/1072239501851758653/caption.gif?ex=67cc9c5a&is=67cb4ada&hm=d2a7ab87fbd6c8ee3c36b0cbae0a5d5f37ef3dcb2675c79af29bb5e4b43cbe56&', 'https://media.discordapp.net/attachments/514133658529955860/1062394076458131466/caption.gif?ex=67cd0c56&is=67cbbad6&hm=0663ec167e0ae83d51e6148b4c1c1e79257d2942d3d21bfcadacb8862d9c2914&', 'https://media.discordapp.net/attachments/554288956926066708/1064562754058465300/tomatonline.gif?ex=67cd0713&is=67cbb593&hm=b5b615d74141ecb4930c84a08fcedf674c41f3a57bba1b2ea6e1f9448dd676e3&', 'https://media.discordapp.net/attachments/514133658529955860/1060233189500653639/caption.gif?ex=67cd18da&is=67cbc75a&hm=2ac5c0e47a65845a7373793e77fbfda89e1e56ac8810644ea4cbeef06765adf4&', 'https://media.discordapp.net/attachments/514133658529955860/1062394612049793044/caption.gif?ex=67cd0cd5&is=67cbbb55&hm=a66061888b8ef2400012cde1c69dcc038172899cd50b3cb3e415df2009a3b514&', 'https://tenor.com/view/fat-herobrine-gif-18363356', 'https://discord.com/channels/967091313038196796/1253099639000006697/1346842584655462450', 'https://discord.com/channels/967091313038196796/1042878735965245512/1339264860487291002', 'https://cdn.discordapp.com/attachments/697785285962104872/1300415408918237204/ezgif.com-animated-gif-maker.gif?ex=67cccd7a&is=67cb7bfa&hm=9ec5682253599de080d0b055b70b97f1d27964644012ee23b8e64a19fe1761df&', 'https://www.twitch.tv/mrtomit/clip/RealRelentlessCockroachYouDontSay-3UQHDUhVee5eqZW7', 'https://www.twitch.tv/mrtomit/clip/FrozenZanyGrassDancingBanana-PMeBkuwbmAXhuAvR', 'https://tenor.com/view/amor-gif-10758667656717415642', 'https://tenor.com/view/lie-detector-gif-9388384639890532829', 'https://www.twitch.tv/mrtomit/clip/BashfulIgnorantFalconPeoplesChamp-eFi5sXgyMJ5gJIC-', 'https://www.youtube.com/watch?v=-BP7DhHTU-I', 'https://tenor.com/view/fall-falling-fallen-kingdom-fallen-kingdom-gif-6774652182841014167', 'https://media.discordapp.net/attachments/1018882963259281459/1100078685018673273/vzriv_pekarni2.gif?ex=67cd08dc&is=67cbb75c&hm=ab172db2fb30ac76bbc18d8288ffabb5a70c96a9c6818e095f1992b200f01021&', 'https://tenor.com/view/%D1%82%D1%8B%D0%BE%D1%82%D0%BF%D1%80%D0%B0%D0%B2%D0%BB%D1%8F%D0%B5%D1%88%D1%8C%D1%81%D1%8F%D0%B2%D1%83%D0%B3%D0%BE%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5-gif-26526641', 'https://tenor.com/view/fish-react-fish-react-him-thanos-gif-26859685', 'https://www.youtube.com/watch?v=DUgcNM-3d5E', 'https://media.discordapp.net/attachments/1018882963259281459/1135203069362180166/bonobo_activities.gif?ex=67ccef7e&is=67cb9dfe&hm=e3d3f2fccddce11abcd270862e80009269670c2e0162100516f22a1ddd78960c&', 'https://media.discordapp.net/attachments/1051934380924338186/1072860017075691580/tomat_usnul.gif?ex=67cce400&is=67cb9280&hm=6bb218dc13b718c9600ffb89c3282dadf16e75c97df1df8615946192b2dd7645&', 'https://youtu.be/H4iWAbaVIMU', 'https://discord.com/channels/967091313038196796/1202188402364268544/1227981517133975592', 'https://youtu.be/WhVZna5ONlk', 'https://youtu.be/Z5cPWkhM4X0', 'https://cdn.discordapp.com/attachments/810191795727237120/1085276447989583952/im_so_excited_about_my_super_weapon_that_will_take_over_watergrad_that_i_wrote_a_song_about_it.mp4?ex=67cc93f4&is=67cb4274&hm=550433c58a90d4ed7423d4a0d5f11acbfc25ad6d5094515a2dd9be959986f339&', 'https://media.discordapp.net/attachments/1051934380924338186/1072853000802025512/pov_you_opened_a_chest_in_facility.gif?ex=67ccdd78&is=67cb8bf8&hm=f2fa4bf2fa68b5cca343b86d5dd99925db9f5e662a3e6b95fe1ecf38326f24c6&', 'https://youtu.be/AitziTN7gX4', 'https://media.discordapp.net/attachments/967091313038196799/1056984343056224256/image.png?width=960&height=330&ex=67cd24a1&is=67cbd321&hm=13c51cd86c4b050977c48c7255d8442a4a51248f48a990b2087fe3b513110a16&', 'https://www.youtube.com/watch?v=LF_zoIAZvBs', 'https://www.youtube.com/watch?v=o-Kz7suDYXE', 'https://cdn.discordapp.com/attachments/1052554161247486022/1052554161360752670/ooomeme.png?ex=67ccd8b3&is=67cb8733&hm=77058ce38a8b829f5306596c4378aa85b916232ee8dccd621c71c7fee47d99f8&', 'https://cdn.discordapp.com/attachments/967165979870236732/970292304629858324/Minecraft__1.17_-___2021-06-21_21-03-52.mp4?ex=67ccd8e0&is=67cb8760&hm=24bcd7d9ac3e398974e6e232204bb00b808515686209c1125366a3f0dfb532e1&', 'https://cdn.discordapp.com/attachments/1236673315146301480/1347574003551965206/image.png?ex=67ccfa57&is=67cba8d7&hm=ca8ac2f60377eba7439becbf347695f6154a70b271aa1837c75068a109bd5bbb&','https://cdn.discordapp.com/attachments/967091313038196799/967555498427691008/IMG_20220424_013929.jpg?ex=67ccc747&is=67cb75c7&hm=c973a4c26ed6da659bc2a78f7b12a8afaf9b8dc7ebd4121fd316d7df8dfe3e7a&', 'https://cdn.discordapp.com/attachments/967091313038196799/985660594776604672/2022-06-13_00.21.41.png?ex=67ccb9f6&is=67cb6876&hm=00c91abc5c24684a410472a3354072ecae208bb2e410fa21e0c527f53e437f8e&', 'https://cdn.discordapp.com/attachments/967091313038196799/983821042835394660/unknown.png?ex=67cca03f&is=67cb4ebf&hm=f6fb9bdfed29f7db74516c8d9bf2b0d200252f806757293f2d571ee097f8b818&', 'https://cdn.discordapp.com/attachments/973855354242883614/988149740984205393/unknown.png?ex=67cc8da9&is=67cb3c29&hm=91f2b73d2c909bb82d027dfde6274f7eb99815dcad1144d29af49293aa1a533f&', 'https://cdn.discordapp.com/attachments/967091313038196799/986727094694326334/unknown.png?ex=67cca6b7&is=67cb5537&hm=836b8de365b81e97007333dc1cdc33c1b283c3dfca324e019fe3c31e4f89088b&', 'https://cdn.discordapp.com/attachments/967091313038196799/1004073870132772975/unknown.png?ex=67cd22e9&is=67cbd169&hm=57da359e97aba90c4f5fe280b743c878f70c057d82b90c0da70d1b92a56ec461&', 'https://cdn.discordapp.com/attachments/973855354242883614/993236278164328539/2022-07-03_20.51.41.png?ex=67cc99de&is=67cb485e&hm=778ef073e1f0cd64b6abba68f0fa10b192fa14ff8cf4a9219a4e00dbf7388118&', 'https://media.discordapp.net/attachments/973855354242883614/995735240104488970/2022-07-07_00.59.09.png?ex=67cd1f75&is=67cbcdf5&hm=731044107c6a807a29ae6d534068f59be4c42ac0e036bedcb2e4c14a87001a0c&=&format=webp&quality=lossless&width=1708&height=881', 'https://cdn.discordapp.com/attachments/967091313038196799/1042569919386107966/image.png?ex=67ccc766&is=67cb75e6&hm=4aa89dee5385f99ad9da4923cc5f973bdbf8d7bd89e0d94b3096051b08779fa0&', 'https://cdn.discordapp.com/attachments/1053245957808070656/1053245958235902012/unknown_7.png?ex=67ccb9fc&is=67cb687c&hm=1a21aea8f75771c265e2b1321397e57d2cf828091929ca8bda20080f2fcc85b5&', 'https://cdn.discordapp.com/attachments/967091313038196799/1051924028794863777/image.png?ex=67cc8818&is=67cb3698&hm=5383778cd503a109ec36291769daec85c015e937da92117ce3ddfc7aef127f2c&', 'https://cdn.discordapp.com/attachments/1042878735965245512/1057312190962610227/unknown_1672153136569.png?ex=67cd0476&is=67cbb2f6&hm=50323c2d9777b362055f02908925b34f36edda71b0c8657943c4158383cbf1cb&', 'https://cdn.discordapp.com/attachments/1042878735965245512/1055105492202033212/94cef12ad874169a.gif?ex=67cce650&is=67cb94d0&hm=3160a5941df23b5c56683231405db5d64b528d976d9c568f4cf34df1f12ca3ed&', 'https://media.discordapp.net/attachments/1058470259872518204/1058470260803653754/2022-12-30_21.35.02.png?ex=67cc9dbf&is=67cb4c3f&hm=3d329aaf17bb0ea212b85ce83cf63a33b5b655249e4f5f1405a9b04c9cd1ca90&=&format=webp&quality=lossless&width=1708&height=881', 'https://cdn.discordapp.com/attachments/1042878735965245512/1063512171293720718/2023-01-09_01.16.41.png?ex=67cd2924&is=67cbd7a4&hm=eb48612a63ad8f09525b24f62c900e929ed6e077d51956a57d6d0cfad9123759&', 'https://cdn.discordapp.com/attachments/973855354242883614/1064904808215085096/caption-3.gif?ex=67ccf423&is=67cba2a3&hm=49962465f554cd00058178c749809c0f6c2e1ca6ae0b9f6a1b3a17b05a7c77eb&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1067036219139162122/IMG_20230123_140035.jpg?ex=67cccc2b&is=67cb7aab&hm=077ff62e90cf1b168af2d7f44b5c918a3ee3eb4816a671d25861cc42f382b2e3&', 'https://cdn.discordapp.com/attachments/1042878735965245512/1069039172146430062/image.png?ex=67ccd550&is=67cb83d0&hm=8e04d568ed748cd35512bab24fa5c6b7faef45f98b65dc8529cb4448e5dc466f&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1068543204389032067/2022-05-15_18.png?ex=67cd01a8&is=67cbb028&hm=4f9b4335aa91c53874a58f31b605a553fe0bf0f1c839accbb99f88bc0cef39af&',
             'https://cdn.discordapp.com/attachments/973855354242883614/1070045755236167680/IMG_20230131_211925.jpg?ex=67cc8a44&is=67cb38c4&hm=ec8e711eb3f5d16985ec1ee778480ee8d0a3f8cad3140778e864c96288764fef&', 'https://cdn.discordapp.com/attachments/1042878735965245512/1074406524526534808/image.png?ex=67cc958c&is=67cb440c&hm=257f133c45c9b81c26071638dd587708c1b5992ea8bf086ade7b272bea401fa8&', 'https://cdn.discordapp.com/attachments/1042878735965245512/1075127851386425405/image.png?ex=67cc9256&is=67cb40d6&hm=82ddfb5663ea278a201baf7d4d78b29b5e65a708b5ee01ba22c5bffeb1d38931&', 'https://cdn.discordapp.com/attachments/1042878735965245512/1080147544346202275/image.png?ex=67cd090a&is=67cbb78a&hm=8c140a13688d3008437fc02cebf6a35f884a51714a0f013f8d126b16e5d72f2e&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1081255204395159643/image.png?ex=67cd1c21&is=67cbcaa1&hm=1110ffe02823f5e114de5036481e65ab56903ada9fed14892a18acf53e9edc2d&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1081260176537047200/image.png?ex=67cd20c2&is=67cbcf42&hm=d5bb5c3cecb1f0f825d7c2647bd8506411357db5bc01585e67c55949283b9a96&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1093821298171453450/566535385_456239226.mp4?ex=67ccaeb7&is=67cb5d37&hm=ddd3258f42517ef49795faeadf0c48fd45ad5e2d66ec30e9018fb2ee0c09505e&', 'https://cdn.discordapp.com/attachments/1052159403584913428/1098346753939492925/image.png?ex=67ccaaa0&is=67cb5920&hm=32a24682c965cb92a14c029368fb82642635bf557adaae2f615ea6a66a5abec5&', 'https://cdn.discordapp.com/attachments/1052159403584913428/1111429447820791878/image.png?ex=67ccccd5&is=67cb7b55&hm=e6ce3c7114697abb1d7d501c23d401e590bc49524971e10194f5e04776d9fb52&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1093914717715693659/image.png?ex=67cd05b8&is=67cbb438&hm=fdfe5357b5d36e5ccc61cbf3b0425568c91ffde7a47a228c68ed33d13000edf6&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1093914657414193303/image.png?ex=67cd05aa&is=67cbb42a&hm=5167ff6c852dc85736772912498f1de7e8ebad306603bc24c98d71e35966e3f9&', 'https://cdn.discordapp.com/attachments/973855354242883614/1114576467167297636/IMG_20230603_180347.jpg?ex=67cd0af9&is=67cbb979&hm=72d0c6293e7ac57fefc77b4dc5cd3023a5dc570fe19aaaa199e9c45468808dba&', 'https://cdn.discordapp.com/attachments/973855354242883614/1113603484500099122/image.png?ex=67cccc90&is=67cb7b10&hm=5d8ff32583ebfdfac83a8f796e72836261774bd6cf798cfb31e3d57a38e279a5&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1113575593636798574/image.png?ex=67ccb296&is=67cb6116&hm=6783cb181a035ade67963207175ef0c8b748834df41b2cf44b2408dcf36643b1&', 'https://cdn.discordapp.com/attachments/1115735315525672980/1115740961897726063/2022-11-17_20.10.56.png?ex=67ccaa3e&is=67cb58be&hm=4875380611634577692ac7b22e0a65b4d9ad6f774c1b430f19dedac8a1a17771&', 'https://cdn.discordapp.com/attachments/1115735315525672980/1115739013744173077/2022-06-08_19.57.57.png?ex=67cca86e&is=67cb56ee&hm=89aa3a612d1d60da3381ce7a735ec4a6e6ae84cc322f52704165244c14876104&', 'https://discord.com/channels/967091313038196796/1115735315525672980/1115738891597651968', 'https://cdn.discordapp.com/attachments/1115735315525672980/1115737126923944138/2022-04-25_19.49.02.png?ex=67cca6ac&is=67cb552c&hm=4a260b6a9440bd60b2180e898df842369523dedf455189e7b9dbcbbb9febab99&', 'https://cdn.discordapp.com/attachments/1042878735965245512/1133723612185116682/IMG_20230726_163236.jpg?ex=67ccd3a4&is=67cb8224&hm=a54fd3d9d432667d3b5a293e34642166b1aee6bcc5ecb0389f3498c9cd9fdbb6&', 'https://cdn.discordapp.com/attachments/1042878735965245512/1134892521558913155/image.png?ex=67cd1fc6&is=67cbce46&hm=facdace071ec82728b1530294a5188f2a7133c538bc1f23299703b860979a767&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1154808442603712553/image.png?ex=67cd116c&is=67cbbfec&hm=848e67876d4682aa96d16dc4d8078c3a0e8251017edcb8f3d67c1b10b5ad85b0&', 'https://cdn.discordapp.com/attachments/1042878735965245512/1153014381756555305/nakurilsa2.png?ex=67cd2212&is=67cbd092&hm=5b91dad4e5191b00e467fd852b3949fa1acfbe293cb17c2e65c40944d92f5e57&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1156561238885666916/IMG_20230927_150045.jpg?ex=67ccda57&is=67cb88d7&hm=9bfa1f73d3e47735a38ecb31a240c00db6c6bab2fff51045c98b1bd41acce6ed&', 'https://cdn.discordapp.com/attachments/1027313548315086878/1160709997370544220/tiny-nerd.gif?ex=67ccc8ec&is=67cb776c&hm=6686345c1acb12b7ba995a825857704914c3692f9ea3942bdf10c37a0e2fd748&', 'https://cdn.discordapp.com/attachments/1042878735965245512/1160684305496932484/area_render.png?ex=67ccb0fe&is=67cb5f7e&hm=8143d3b200c855fb56f3b96fbb85298080f728e98ef78a87beae2047a1c9a87d&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1168834219053678602/1168833142610743377remix-1698742188237.png?ex=67ccad71&is=67cb5bf1&hm=522b9da0cc16b16c9e0b566e851d1943fef5c3ef6ec0b433342ab4e2f7140bb2&', 'https://tenor.com/view/%D0%B4%D0%BE%D0%B2%D0%BE%D0%B4-tenet-christopher-nolan-nolan-%D0%BE%D0%B1%D1%81%D1%83%D0%B6%D0%B4%D0%B0%D0%B5%D0%BC-gif-24881957', 'https://cdn.discordapp.com/attachments/1051934380924338186/1184878465833508934/image.png?ex=67cd09d0&is=67cbb850&hm=7e549305345b4cb675c0feb1951c47e7b37fe0e5d94d75932d7c31977ef3054b&', 'https://cdn.discordapp.com/attachments/1051934380924338186/1195773410685493321/image.png?ex=67cd1f85&is=67cbce05&hm=d1867ce3b884e21eeefea2907e6563e54bf75ee528b491cb9ff2b3871df8068c&', 'https://cdn.discordapp.com/attachments/1109099791419457627/1197499975526006825/IMG_20240118_141158_874.jpg?ex=67ccd002&is=67cb7e82&hm=dfda079a68b731ff00a1e53220fa10234077941d0849a0f60769dc6023526fa6&', 'https://tenor.com/view/gorilla-reaction-gorilla-shocked-appauled-eating-pepper-gif-2230596277954293584', 'https://cdn.discordapp.com/attachments/1042878735965245512/1200698743687761920/image.png?ex=67cc9598&is=67cb4418&hm=db5c3e6f3188056cf96371f8398c6e8dc852546d0cc0d93efab08741197b727f&']
    await ctx.send(random.choice(links))

@client.hybrid_command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def shop(ctx):
    embed = myshop.embed


    class BackButton(discord.ui.View):
        def __init__(self, author, timeout=None):
            super().__init__(timeout=timeout)
            self.author = author

        @discord.ui.button(label='Назад', style=discord.ButtonStyle.success)
        async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(embed=myshop.shop_view(), view=shopButtons(ctx.author, timeout=None))

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

        @discord.ui.button(label='Купить', style=discord.ButtonStyle.success)
        async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = discord.Embed(color=Color.dark_purple(), title="Магазин", description=f"Вы купили {current_emoji}")
            user_data = inventory_ref.child(str(self.author.id)).get()
            multiplier, word, name, way_to_sell, func, icon, price = items.get(current_emoji)
            fish_emojis = ['🐟', '🐠', '🐡', '🪼', '🦈', '🐙', '🦐']
            economy_data = economy_ref.child(str(self.author.id)).get()
            if economy_data is None:
                embed = discord.Embed(color=Color.dark_purple(), title="Магазин",
                                      description=f"У вас не хватает денег!")
                await interaction.response.edit_message(embed=embed, view=None)
                return
            else:
                current_coins = economy_data['coins']
                if int(current_coins) < int(price):
                    embed = discord.Embed(color=Color.dark_purple(), title="Магазин",
                                          description=f"У вас не хватает денег!")
                    await interaction.response.edit_message(embed=embed, view=None)
                    return


            if user_data is None:
                if current_emoji in fish_emojis:
                    inventory_ref.child(str(self.author.id)).set(
                        {f'{current_emoji}' + str(int(time.time() * 1000)): int(int(price) * random.random())})
                    current_coins = economy_data['coins']
                    economy_ref.child(str(self.author.id)).set({
                        'coins': current_coins - int(price)
                    })
                    await interaction.response.edit_message(embed=embed, view=None)
                else:
                    inventory_ref.child(str(self.author.id)).update({f'{current_emoji}' + str(int(time.time() * 1000)): int(int(price) * random.random())})
                    current_coins = economy_data['coins']
                    economy_ref.child(str(self.author.id)).set({
                        'coins': current_coins - int(price)
                    })
                    await interaction.response.edit_message(embed=embed, view=None)
            else:
                if current_emoji in fish_emojis:
                    inventory_ref.child(str(self.author.id)).update(
                        {f'{current_emoji}' + str(int(time.time() * 1000)): (int(price) - int(random.randint(19, 30)))})
                    current_coins = economy_data['coins']
                    economy_ref.child(str(self.author.id)).set({
                        'coins': current_coins - int(price)
                    })
                    await interaction.response.edit_message(embed=embed, view=None)
                else:
                    new_item = inventory_ref.child(str(self.author.id)).update({
                        f'{current_emoji}' + str(int(time.time() * 1000)): int(int(price) * random.random())
                    })
                    current_coins = economy_data['coins']
                    economy_ref.child(str(self.author.id)).set({
                        'coins': current_coins - int(price)
                    })
                    await interaction.response.edit_message(embed=embed, view=None)

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

    class shopButtons(discord.ui.View):
        def __init__(self, author, timeout=None):
            super().__init__(timeout=timeout)
            self.author = author

        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji=str(myshop.chosen_keys[0][5]))
        async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
            global current_emoji
            current_emoji = myshop.chosen_keys[0][5]
            item_info = discord.Embed(color=Color.dark_purple(), title=myshop.chosen_keys[0][2], description=None)
            item_info.add_field(name="Описание:", value=myshop.chosen_keys[0][3], inline=True)
            await interaction.response.edit_message(embed=item_info, view=BackButton(ctx.author, timeout=None))

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji=str(myshop.chosen_keys[1][5]))
        async def second(self, interaction: discord.Interaction, button: discord.ui.Button):
            global current_emoji
            current_emoji = myshop.chosen_keys[1][5]
            item_info = discord.Embed(color=Color.dark_purple(), title=myshop.chosen_keys[1][2], description=None)
            item_info.add_field(name="Описание:", value=myshop.chosen_keys[1][3], inline=True)
            await interaction.response.edit_message(embed=item_info, view=BackButton(ctx.author, timeout=None))

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji=str(myshop.chosen_keys[2][5]))
        async def third(self, interaction: discord.Interaction, button: discord.ui.Button):
            global current_emoji
            current_emoji = myshop.chosen_keys[2][5]
            item_info = discord.Embed(color=Color.dark_purple(), title=myshop.chosen_keys[2][2], description=None)
            item_info.add_field(name="Описание:", value=myshop.chosen_keys[2][3], inline=True)
            await interaction.response.edit_message(embed=item_info, view=BackButton(ctx.author, timeout=None))

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

    msg = await ctx.send(embed = embed, view=shopButtons(ctx.author, timeout=None))
    await task
    embed = discord.Embed(title="Магазин закрыт на обнову",
                               description="Введите ещё раз команду !shop для обновления магазина")
    await msg.edit(embed=embed, view=None)
async def shop_func():
    await asyncio.sleep(21600)

async def periodic_task():
    global shop_items
    global task
    while True:
        shop_items = myshop.initialize_shop()
        print("Shop changed")
        task = asyncio.create_task(shop_func())
        await task


client.run(os.environ['BOT_TOKEN'])
