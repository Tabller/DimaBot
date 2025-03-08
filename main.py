import copy
from datetime import datetime
from datetime import timedelta
# from tkinter.ttk import Button
import discord
from threading import Timer
import itertools
import ast
import re
import asyncio
import os
import firebase_admin
from discord.ext.commands import has_any_role
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
from discord.enums import ButtonStyle
from discord.ext import commands, tasks
from discord.utils import get
from discord import Webhook, SyncWebhook, Interaction, Color
import aiohttp
import random
import json
import time
from dotenv import load_dotenv
import os
from collections import Counter
from string import digits

from google_crc32c.python import value
from rsa.randnum import randint
from discord import app_commands
import logging

load_dotenv(dotenv_path='/root/DimaBot/.env')

intents = discord.Intents.all()
intents.message_content = True

client = commands.Bot(command_prefix='!', intents=intents, help_command=None)
url = os.environ['WEBHOOK_URL']


service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

service_account_dict = json.loads(service_account_json)

cred = credentials.Certificate(service_account_dict)
firebase_admin.initialize_app(cred, {
      'databaseURL': f'{os.getenv("LINK_DATABASE")}'
  })
games_ref = db.reference('games')
economy_ref = db.reference('economy')
inventory_ref = db.reference('inventory')
penalty_ref = db.reference('penalty')

@client.event
async def on_ready():
    print(f'Bot {client.user} is online.')
    client.loop.create_task(periodic_task())
    try:
        synced = await client.tree.sync()
        print(f'Synced {len(synced)} interaction command(s).')
    except Exception as exception:
        print(exception)
    activity = discord.Game("ponos")
    await client.change_presence(activity=activity)


@client.event
async def on_message(message):
    if message.guild.id == 967091313038196796:
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


@client.hybrid_command()
async def test(ctx, *, arg):
    await ctx.send(arg)




@client.hybrid_command()
@commands.has_any_role(968045914591723582)
async def verify(ctx, *, nick):
    if str(ctx.channel.id) == '1109099791419457627':
        if len(nick) < 33:
            embed4 = discord.Embed(description="Вас добавили на рассмотрение. Ожидайте сообщения в ЛС!", colour=discord.Colour(int('5BC1FF', 16)))
            await ctx.send(embed=embed4)
            channel = client.get_channel(1236673315146301480)
            id_thing = ctx.author.id
            guild = client.get_guild(967091313038196796)
            member = guild.get_member(ctx.author.id)
            gaming_role = 1054830462108971149
            not_gaming_role = 968045914591723582
            game_admin_user = client.get_user(347365756301737994)
            class Buttons(discord.ui.View):
                @discord.ui.button(label='Подтвердить', style=discord.ButtonStyle.success)
                async def respond1(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.get_role(1053297629112569926):
                        view.stop()
                        button.disabled = True
                        user = client.get_user(id_thing)
                        decline_button = None
                        for child in self.children:
                            if type(child) == discord.ui.Button and child.label == "Отклонить":
                                decline_button = child
                                child.disabled = True
                                break

                        embed3 = discord.Embed(description="Вас добавили в вайтлист.\nПриятной игры!", colour=discord.Colour(int('5BC1FF', 16)))
                        await interaction.message.edit(content=f'Вы приняли в вайтлист (я надеюсь).', embed=None, view=self)
                        if user:
                            await user.send(embed=embed3)
                            await member.edit(nick=nick)
                            await member.remove_roles(member.guild.get_role(not_gaming_role))
                            await member.add_roles(member.guild.get_role(gaming_role))

                @discord.ui.button(label='Отклонить', style=discord.ButtonStyle.danger)
                async def respond2(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.get_role(1053297629112569926):
                        view.stop()
                        user = client.get_user(id_thing)
                        await interaction.channel.send('Введите причину:')

                        def check(m):
                            return m.author.id == interaction.user.id

                        message = await client.wait_for('message', check=check)
                        embed2 = discord.Embed(description=f"Вас **не добавили** в вайтлист, но вы всё ещё можете общаться на сервере.\nПричина: {message.content}", colour=discord.Colour(int('5BC1FF', 16)))
                        button.disabled = True
                        accept_button = None
                        for child in self.children:
                            if type(child) == discord.ui.Button and child.label == "Подтвердить":
                                accept_button = child
                                child.disabled = True
                                break
                        await interaction.message.edit(content=f'Вы **не приняли** {iterate(ctx.author.display_name)} в вайтлист.', embed=None, view=self)
                        if user:
                            await user.send(embed=embed2)
            view = Buttons(timeout=None)
            embed = discord.Embed(description=f'Пользователь: **{iterate(ctx.author.display_name)}** \nНик: **{iterate(nick)}**', colour=discord.Colour(int('5BC1FF', 16)))
            await channel.send(content=game_admin_user.mention,embed=embed, view=view)
        else:
            await ctx.send('слишком длинный никнейм')
    else:
        await ctx.send('юзай в другом канале')

@verify.error
async def verify_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send('ты и так верифицирован')

@client.command()
async def detect(ctx, user: discord.Member):
    await ctx.send(user)


dict = {}
game_list = []


class Menu(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None


@client.command()
async def help(ctx, member: discord.Member = None):
    if member == None:
        member = ctx.author

    name = member.display_name
    pfp = member.display_avatar

    commands_twitch = {
        "/submit [игра]": "Предложить игру для стрима в канал <#1185909058910310420>",
        "/showlist": "Посмотреть список предложенных игр."
    }
    commands_rpg = {
        "!balance (@юзер)": "Проверить свой карман (на наличие денег).",
        "!fish": "Рыбалка симулятор.",
        "!sell [:emoji:/inventory]": "Продать предмет(ы)/весь инвентарь",
        "!leaderboard": "Просмотр таблицы монет",
        "!shop": "Просмотр магазина, который обновляется каждые 6 часов.",
        "!craft [2-3 :emoji:]": "Создать предмет, если рецепт окажется верным."
    }
    commands_admin = {
        "!клетка [@юзер] [время [s/m/h/d]] (бананы) (причина)": "Отправить человека в то самое место..."
    }

    commands_other = {
        "!feedback [текст]": "Отправить фидбек о боте (идеи, впечатления и так далее).",
        "!meme": "Отправляет рандомный мем из коллекции."
    }

    embed = discord.Embed(title='димабот ft. Томатские Угодья',
                          description='Здесь находится вся актуальная информация о ссылках, которые ведут на томата.',
                          colour=discord.Colour(int('a970ff', 16)))

    embed.add_field(name="Команды категории Твич", value="дима подписчик", inline=True)
    for command, description in commands_twitch.items():
        embed.add_field(name=f"`{command}`", value=f"{description}", inline=False)
    embed.add_field(name="Команды категории Экономика", value="дима рпг игра", inline=True)
    for command, description in commands_rpg.items():
        embed.add_field(name=f"`{command}`", value=f"{description}", inline=False)
    embed.add_field(name="Команды категории Администрация", value="дима с молотком бана", inline=True)
    for command, description in commands_admin.items():
        embed.add_field(name=f"`{command}`", value=f"{description}", inline=False)
    embed.add_field(name="Команды категории Другие", value="дима с магическим шаром", inline=True)
    for command, description in commands_other.items():
        embed.add_field(name=f"`{command}`", value=f"{description}", inline=False)


    view = Menu()
    view.add_item(
        discord.ui.Button(label='Twitch Channel', style=discord.ButtonStyle.link, url='https://www.twitch.tv/mrtomit'))
    await ctx.send(embed=embed, view=view)

@client.hybrid_command()  # ЛИСТ СПИСКА
async def showlist(ctx):
    message = ''
    all_games = games_ref.get()
    if all_games:
        for user_id, games in all_games.items():
            for game in games.values():
                message += f"{game}\n"
        await ctx.send(message)
    else:
        await ctx.send('Лист пуст')


# @list.error  # ОШИБКА В ЛИСТЕ
# async def list_error(ctx, error):
#    if not len(game_list) == 0 and not isinstance(error, commands.CommandInvokeError):
#        await ctx.send(f'Лист помер по причине: {error}')
#    elif isinstance(error, commands.CommandInvokeError):
#        async def backup_plan():
#            message = ''
#            global game_list
#            temporary_game_list = ()
#            keys, values = zip(*dict.items())
#            for item in values:
#                temporary_game_list = temporary_game_list + item
#            for item in temporary_game_list:
#                game_list.append(item)
#            with open("ponos.txt", "w") as file:
#                for item in game_list:
#                    file.write(f'{str(item)}\n')
#            with open("ponos.txt", "rb") as file:
#                await ctx.send(file=discord.File(file, "ponos.txt"))
#        await backup_plan()
#    else:
#        await ctx.send('Лист пуст')



def iterate(author):
    word = ''
    for i in author:
        if i in '~*_`|>':
            word = word + '\\'
            word = word + i
        else:
            word = word + i
    return word

@client.hybrid_command()
async def submit(ctx, *, game):
    result = ''
    if len(str(game)) < 64:
        pattern = "(?P<url>https?://[^\s]+)"
        r1 = re.split(pattern, game)
        r2 = re.findall(pattern, game)
        for item in r1:
            if item in r2:
                result = result + '<' + item + '>'
            else:
                result = result + item
        # games_ref.child(str(ctx.author.id)).push(str(result).replace('\n', ''))
      
    user_data = games_ref.child(str(ctx.author.id)).get()

    if user_data is None:
        games_ref.child(str(ctx.author.id)).set({
            '-L' + str(int(time.time() * 1000)): str(result).replace('\n', '')  # Add the new game with a timestamp
        })
    else:
        # Get the current game count
        game_count = len(user_data.keys())

        if game_count >= 3:
            print(user_data.keys())
            print(user_data)
            summarize = [key for key in user_data.keys()]
            oldest_game = min(summarize)
            games_ref.child(str(ctx.author.id)).update({
                oldest_game: None,
                '-L' + str(int(time.time() * 1000)): str(result).replace('\n', '')
            })
        else:
            # If the user has less than 3 games, add the new game
            games_ref.child(str(ctx.author.id)).update({
                '-L' + str(int(time.time() * 1000)): str(result).replace('\n', '')  # Add the new game with a timestamp
            })

    display_namee = iterate(ctx.author.display_name)
    embed1 = discord.Embed(description=f'**{display_namee}** предложил игру **{str(result)}**',
                           colour=discord.Colour(int('ec5353', 16)))
    if len(str(game)) < 64:
        message = await ctx.send(embed=embed1)
        message_id = message.id
        await message.add_reaction('tomatjret:1098375901248487424')
    else:
        await ctx.send(f'{ctx.author.mention} заебёшь')

@client.hybrid_command()
async def delete_item(ctx, *, suggestion):
    user_data = games_ref.child(str(ctx.author.id)).get()
    if user_data is not None:
        t_list = user_data
        pattern = "(?P<url>https?://[^\s]+)"
        r1 = re.split(pattern, suggestion)
        r2 = re.findall(pattern, suggestion)
        for item in r1:
            if item in r2:
                result = result + '<' + item + '>'
            else:
                result = result + item
        if result in t_list:
            t_list.pop(t_list.index(result))
            user_data.child(str(ctx.author.id)).set(t_list)
            await ctx.send(f'Успешно удалён элемент {result}.')
        else:
            await ctx.send(f'Элемент не найден в вашем списке...')
    else:
        await ctx.send(f'User не найден в списке...')

@delete_item.error
async def delete_item_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(error)

@client.command()
@commands.is_owner()
async def clear(ctx):
    games_ref.delete()
    await ctx.send('Лист очищен.')

@client.command()
@commands.is_owner()
async def getdict(ctx):
    await ctx.send("hello")

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('поносно не можешь использовать')


@client.hybrid_command()
async def feedback(ctx, *, text):
    async def ponos(prompt, username, avatar):
        channel = client.get_channel(ctx.channel.id)
        web_temporary = await client.fetch_webhook(1199759425519489074)

        class AnswerButton(discord.ui.View):
            @discord.ui.button(label='ответить', style=discord.ButtonStyle.success)
            async def respond3(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.channel.send('Введите ответ:')

                def check(m):
                    return m.author.id == interaction.user.id

                message = await client.wait_for('message', check=check)
                embed4 = discord.Embed(description=f'{message.author.display_name}: {message}')
                await channel.send(embed=embed4)
        view = AnswerButton(timeout=None)
        await web_temporary.send(content=prompt, username=username, avatar_url=avatar, view=view)
    await ponos(prompt=text, username=ctx.author.display_name, avatar=ctx.author.display_avatar)
    await ctx.send('фидбек отправлен (наверное)')


items = {
            '👢': [1, "монет", "грязный ботинок", "Грязные ботинки штамповали тысячами в Австралии. Неизвестно почему, но все они оказались в море. Спасите морской биоценоз — соберите их все!", "func", '👢', "6"],
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
            '🎩': [2.45, "монет", "шляпникус","Я не знаю, что это, но это точно не из нашего мира. Может быть, оно обладает каким-либо функционалом? Или используется для чего-то? Кто знает...", "func", '🎩', "872"],
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
            '🍣': [1.28, "монет", "сашими", "DIY, прямиком из-под ножа!", "func", '🍣', "155"]

        }

@client.command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def craft(ctx, *, emoji):
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
        frozenset(['🐟', '🐠']): items.get('🍣')

    }
    ingredients = set(emoji.replace(" ", ""))
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
            inventory_data = inventory_ref.child(str(ctx.author.id)).get()

            if user_data is None:
                economy_ref.child(ctx.author.id).set({'coins': 0})
            self.how_many = random.randint(1, 3)
            self.game_run = True
            self.fish_y = None
            self.fish_x = None

            self.map_one_coordinates = [["◼️", "◼️", "◼️", "◼️", "◼️", "☀️", "◼️"],
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
                                   ["🟨", "🟨", "🟨", "🟨", "🟨", "🟨", "🟨"]]

            #global previous_hook
            #global previous_boat

            self.previous_hook = [4, 3]
            self.previous_boat = [2, 3]

        def map_print(self):
            # map_one_coordinates, fish_coord = spawn_fish()
            global line
            count = 0
            line = ''
            for row in self.map_one_coordinates:
                for emoji in row:
                    if count < 7:

                        line = line + f''.join(emoji)
                        count += 1
                    else:
                        line = line + f''.join('\n')
                        line = line + f''.join(emoji)
                        count = 1
            return line

        def move_boat(self, x, y, new_x):
            global raw_map
            raw_map = self.map_one_coordinates
            what_to_change = self.map_one_coordinates[y][x+new_x]
            raw_map[y][x + new_x] = "🛶"
            raw_map[y][x] = what_to_change
            self.previous_boat[1] += new_x
            return raw_map



        def spawn_fish(self):

            choice_x = [0, 6]
            choice_y = [5, 8]
            inventory_data = inventory_ref.child(str(ctx.author.id)).get()

            if inventory_data is None:
                pass
            else:
                fish_rod_list = []
                for key, value in inventory_data.items():
                    new_string = re.sub(r'[0-9]', '', key)
                    fish_rod_list.append(new_string)

                if '🎣' or '📌🎣' in fish_rod_list:
                    fish_emojis = ['🐟','🐟','🐟', '🐟', '🐟', '🐠', '🐠', '🐠', '🐡', '🪼', '👢', '🦐', '🦐', '🐙', '🦈', '🐚', '🐚']
                else:
                    fish_emojis = ['🐟','🐟','🐟', '🐟', '🐟', '🐠', '🐠', '🐠', '🐡', '🪼', '👢']
            # fish_emojis = ['👢']
            global raw_map
            raw_map = self.map_one_coordinates
            self.fish_y = random.choice(choice_y)
            self.fish_x = random.choice(choice_x)
            fish_coords = [self.fish_y, self.fish_x]
            raw_map[self.fish_y][self.fish_x] = random.choice(fish_emojis)


            return raw_map, fish_coords



        def change_coord(self, x, y, new_x, new_y):
            # if previous_hook[0] > 3 or new_y == -1:
            # global game_run
            global raw_map
            what_to_change = self.map_one_coordinates[y+new_y][x+new_x]
            if (what_to_change != "🟨") and (what_to_change != "🪸") and (what_to_change != "◼️") and (what_to_change != "🛶") and (what_to_change != '🐟') and (what_to_change != '🐠') and (what_to_change != '🐡') and (what_to_change != '🪼') and (what_to_change != '👢') and (what_to_change != "🦐") and (what_to_change != '🐙') and (what_to_change != '🦈') and (what_to_change != '🐚'):
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
                        if count < 7:

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
                    if '🎣' in fish_rod_list:
                        cm = random.randint(1, 200) * double_chance()
                    else:
                        cm = random.randint(1, 100) * double_chance()


                if what_to_change == '🐟':

                    line = f'вы поймали карася размером {cm} сантиметров'
                    # base 5 * cm / 10
                    # current_coins = user_data.get('coins', 0)
                    # new_coins = current_coins + 5 * (cm / 10)
                    # economy_ref.child(str(ctx.author.id)).update({'coins': new_coins})

                    inventory_data = inventory_ref.child(str(ctx.author.id)).get()

                    if inventory_data is None:
                        inventory_ref.child(str(ctx.author.id)).set({'🐟' + str(int(time.time() * 1000)): cm})
                    else:
                        current_fish = inventory_ref.child(str(ctx.author.id)).update({
                            '🐟' + str(int(time.time() * 1000)): cm
                        })

                    game_run = False
                    active_games.pop(user_id, None)
                    return line
                if what_to_change == '🐠':
                    line = f'вы поймали брата карася размером {cm} сантиметров'
                    # base 6 * cm / 10
                    # current_coins = user_data.get('coins', 0)
                    # new_coins = current_coins + 6 * (cm / 10)
                    # economy_ref.child(str(ctx.author.id)).update({'coins': new_coins})

                    inventory_data = inventory_ref.child(str(ctx.author.id)).get()

                    if inventory_data is None:
                        inventory_ref.child(str(ctx.author.id)).set({'🐠' + str(int(time.time() * 1000)): cm})
                    else:
                        current_tropical_fish = inventory_ref.child(str(ctx.author.id)).update({
                            '🐠' + str(int(time.time() * 1000)): cm
                        })

                    game_run = False
                    active_games.pop(user_id, None)
                    return line
                if what_to_change == '🐡':
                    line = f'вы поймали рыбу агу ага размером {cm} сантиметров'
                    # base 8 * cm / 10
                    # current_coins = user_data.get('coins', 0)
                    # new_coins = current_coins + 8 * (cm / 10)
                    # economy_ref.child(str(ctx.author.id)).update({'coins': new_coins})

                    inventory_data = inventory_ref.child(str(ctx.author.id)).get()

                    if inventory_data is None:
                        inventory_ref.child(str(ctx.author.id)).set({'🐡' + str(int(time.time() * 1000)): cm})
                    else:
                        current_blowfish = inventory_ref.child(str(ctx.author.id)).update({
                            '🐡' + str(int(time.time() * 1000)): cm
                        })


                    game_run = False
                    active_games.pop(user_id, None)
                    return line
                if what_to_change == '🪼':
                    line = f'вы поймали медузу крутую размером {cm} сантиметров'
                    # base 10 * cm / 10
                    # current_coins = user_data.get('coins', 0)
                    # new_coins = current_coins + 10 * (cm/10)
                    #economy_ref.child(str(ctx.author.id)).update({'coins': new_coins})

                    inventory_data = inventory_ref.child(str(ctx.author.id)).get()

                    if inventory_data is None:
                        inventory_ref.child(str(ctx.author.id)).set({'🪼' + str(int(time.time() * 1000)): cm})
                    else:
                        current_jellyfish = inventory_ref.child(str(ctx.author.id)).update({
                            '🪼' + str(int(time.time() * 1000)): cm
                        })

                    game_run = False
                    active_games.pop(user_id, None)
                    return line

                if what_to_change == '🦐':
                    line = f'вы поймали креветочку размером {cm} сантиметров'
                    # base 11 * cm / 10
                    # current_coins = user_data.get('coins', 0)
                    # new_coins = current_coins + 10 * (cm/10)
                    #economy_ref.child(str(ctx.author.id)).update({'coins': new_coins})

                    inventory_data = inventory_ref.child(str(ctx.author.id)).get()

                    if inventory_data is None:
                        inventory_ref.child(str(ctx.author.id)).set({'🦐' + str(int(time.time() * 1000)): cm})
                    else:
                        current_shrimp = inventory_ref.child(str(ctx.author.id)).update({
                            '🦐' + str(int(time.time() * 1000)): cm
                        })

                    game_run = False
                    active_games.pop(user_id, None)
                    return line

                if what_to_change == '🦈':
                    line = f'Трепещи, rer_5111, я поймать АКУЛУ размером {cm} сантиметров!'
                    # base 18 * cm / 10
                    # current_coins = user_data.get('coins', 0)
                    # new_coins = current_coins + 10 * (cm/10)
                    # economy_ref.child(str(ctx.author.id)).update({'coins': new_coins})

                    inventory_data = inventory_ref.child(str(ctx.author.id)).get()

                    if inventory_data is None:
                        inventory_ref.child(str(ctx.author.id)).set({'🦈' + str(int(time.time() * 1000)): cm})
                    else:
                        current_shark = inventory_ref.child(str(ctx.author.id)).update({
                            '🦈' + str(int(time.time() * 1000)): cm
                        })

                    game_run = False
                    active_games.pop(user_id, None)
                    return line

                if what_to_change == '👢':
                    inventory_data = inventory_ref.child(str(ctx.author.id)).get()

                    if inventory_data is None:
                        inventory_ref.child(str(ctx.author.id)).set({'👢' + str(int(time.time() * 1000)): 5})
                    else:
                        inventory_ref.child(str(ctx.author.id)).update({'👢' + str(int(time.time() * 1000)): 5})


                    line = f'вы поймали грязный ботинок из австралии.'


                    game_run = False
                    active_games.pop(user_id, None)
                    return line

                if what_to_change == '🐚':
                    inventory_data = inventory_ref.child(str(ctx.author.id)).get()

                    if inventory_data is None:
                        inventory_ref.child(str(ctx.author.id)).set({'🐚' + str(int(time.time() * 1000)): 20})
                    else:
                        inventory_ref.child(str(ctx.author.id)).update({'🐚' + str(int(time.time() * 1000)): 20})


                    line = f'вы поймали плавающую ракушку.'

                    game_run = False
                    active_games.pop(user_id, None)
                    return line

                count = 0
                line = ''
                for row in raw_map:
                    for emoji in row:
                        if count < 7:
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
                print(new_embed)
            else:
                await message.edit(embed=new_embed, view=None)
                print(new_embed)
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

role_to_give = "озезяна"

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
    role = discord.utils.get(ctx.guild.roles, name=role_to_give)
    players = discord.utils.get(ctx.guild.roles, name="Игроки")
    unplayers = discord.utils.get(ctx.guild.roles, name="Не игроки")
    saved_roles = member.roles
    if reason is not None:
        if len(reason) > 1024:
            await ctx.reply("что биографию свою пишешь чтоли")
            return



    try:
        new_bananas = int(bananas)
        if new_bananas <= 0 or new_bananas > 99999:
            raise ValueError("емае ну и хрень они пишут")

    except ValueError as e:
        await ctx.reply("что за бред с бананами")
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

    try:
        await member.add_roles(role)
        try:
            await member.remove_roles(players)
            await member.remove_roles(unplayers)
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

        channel = client.get_channel(1330805977011851315)
        if channel:
            embed = discord.Embed(
                title = f"добро пожаловать в говнецо, {member}",
                description = f"вы очевидно в чём-то провинились.",
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

        await asyncio.sleep(time_in_seconds)
        if role in member.roles:
            await member.remove_roles(role)
            if players in saved_roles:
                await member.add_roles(players)
            else:
                await member.add_roles(unplayers)
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


@client.hybrid_command(name = "leaderboard", with_app_command = True)
async def leaderboard(ctx):
    users_data = economy_ref.get()
    users = {}
    for user_id, money in users_data.items():
        user_cool_id = await get_user(user_id)
        users[user_cool_id] = int(money.get("coins"))

    def get_sorted():
        return sorted(users.items(), key=lambda x: x[1], reverse=True)

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

    embed = get_leaderboard_page(current_page, per_page)

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

    await ctx.send(embed=embed, view=LeaderboardView())
@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.has_any_role(1330807076057911296)
async def почистить(ctx, emoji):
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
                        if member:
                            role = discord.utils.get(guild.roles, name="озезяна")
                            if role in member.roles:
                                await member.remove_roles(role)
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


# def singleton(class_):
#     instances = {}
#     def getinstance(*args, **kwargs):
#         if class_ not in instances:
#             instances[class_] = class_(*args, **kwargs)
#         return instances[class_]
#     return getinstance
#
# @singleton
# class MyClass(BaseClass):
#     pass


@client.command()
@commands.cooldown(1, 6, commands.BucketType.user)
async def simulation3(ctx):
    def generate_game():
        fish_emojis = ['🐟', '🐠', '🐡', '🪼']
        fish_game = ['', '', '', '', '', '', '']
        random_index = random.randint(0, 6)
        fish_game[random_index] = random.choice(fish_emojis)
        count = 0
        for emoji in fish_game:
            if emoji in fish_emojis:
                pass
            else:
                fish_game[count] = "🟦"
            count += 1


        global line2
        line2 = ''
        for emoji in fish_game:
            line2 = line2 + f''.join(emoji)
            line2 = line2 + f''.join('\n')
        return line2







    class Buttons(discord.ui.View):
        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji='⬆️')
        async def up(self, interaction: discord.Interaction, button: discord.ui.Button):
            desc = ''
            new_embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)), title=f'фишинг {ctx.author.display_name}', description=desc)
            await message.edit(embed=new_embed)
        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji='⬇️')
        async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
            desc = ''
            new_embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)), title=f'фишинг {ctx.author.display_name}', description=desc)
            await message.edit(embed=new_embed)

    view = Buttons(timeout=None)
    embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)), title=f'фишинг {ctx.author.display_name}',
                          description=generate_game())

    message = await ctx.send(embed=embed, view=view)


# нужно сделать луп здесь шоп короче не лупится почему то можешь проверить типо таймер не выводит.

client.run(os.environ['BOT_TOKEN'])
