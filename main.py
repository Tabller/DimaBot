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

        if all(item in inventory for item in ingredients):
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
            if new_string in items:
                multiplier, word, name, way_to_sell, func, icon, price = items.get(new_string)
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
            what_to_sell[item_name] = quantity

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

                        if new_string in key:
                            multiplier, word, name, way_to_sell, func, icon, price = items.get(new_string)
                            sell_price = int(value * multiplier)
                            current_coins = user_data.get("coins", 0)
                            user_economy_ref.update({"coins": current_coins + sell_price})


                            funny_copy_what_to_sell.pop(key)
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
                    fish_rod_list.append(key)
                if '🎣' in fish_rod_list:
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


@client.command()
@has_any_role(1053297629112569926)
async def лимбо(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="лимбо")
    if role in member.roles:
        await ctx.reply(f"{member.mention} уже в лимбо", ephemeral=True)
        return
    else:
        await member.add_roles(role)

@client.command()
@has_any_role(1053297629112569926)
async def оживить(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="лимбо")
    if not (role in member.roles):
        await ctx.reply(f"{member.mention} не в лимбо", ephemeral=True)
        return
    else:
        await member.remove_roles(role)

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
