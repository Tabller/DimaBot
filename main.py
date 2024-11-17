import discord
import ast
import re
import asyncio
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db
from discord.enums import ButtonStyle
from discord.ext import commands
from discord.utils import get
from discord import Webhook, SyncWebhook
import aiohttp
import json
import time
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='/root/DimaBot/.env')

intents = discord.Intents.all()
intents.message_content = True

client = commands.Bot(command_prefix='!', intents=intents)
url = os.environ['WEBHOOK_URL']


service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

service_account_dict = json.loads(service_account_json)

cred = credentials.Certificate(service_account_dict)
firebase_admin.initialize_app(cred, {
      'databaseURL': f'{os.getenv("LINK_DATABASE")}'
  })
games_ref = db.reference('games')
economy_ref = db.reference('economy')

@client.event
async def on_ready():
    print(f'Bot {client.user} is online.')
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
        await open_account(message.author)
        users = await get_jar_data()
        users[str(message.author.id)]["монетки"] += 1
        with open("moneyjar.json", 'w') as f:
            json.dump(users, f)
    
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
@commands.is_owner()
async def embed(ctx, member: discord.Member = None):
    if member == None:
        member = ctx.author

    name = member.display_name
    pfp = member.display_avatar

    embed = discord.Embed(title='Томатские Угодья',
                          description='Здесь находится вся актуальная информация о ссылках, которые ведут на томата.',
                          colour=discord.Colour(int('a970ff', 16)))
    embed.add_field(name='Команды',
                    value='\n`/submit [игра]` — Предложить игру для стрима в канал <#1185909058910310420> \n`/list` — Посмотреть список предложенных игр.',
                    inline=False)

    view = Menu()
    view.add_item(
        discord.ui.Button(label='Twitch Channel', style=discord.ButtonStyle.link, url='https://www.twitch.tv/mrtomit'))
    await ctx.send(embed=embed, view=view)

@client.hybrid_command()  # ЛИСТ СПИСКА
async def list(ctx):
    message = ''
    all_games = games_ref.get()
    if all_games:
        for user_id, games in all_games.items():
            for game in games.values():
                message += f"'{game}\n"
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
      
    user_data = games_ref.child(key).get()

    if user_data is None:
        # Create a new entry for the user
        games_ref.child(str(ctx.author.id)).set({
            '-L' + str(int(time.time() * 1000)): str(result).replace('\n', '')  # Add the new game with a timestamp
        })
    else:
        # Get the current game count
        game_count = len(user_data.keys())

        # If the user has 3 or more games, remove the oldest game and add the new one
        if game_count >= 3:
            oldest_game_key = list(user_data.keys())[0]  # Get the key of the oldest game
            games_ref.child(str(ctx.author.id)).update({
                oldest_game_key: None,  # Remove the oldest game
                '-L' + str(int(time.time() * 1000)): str(result).replace('\n', '')  # Add the new game with a timestamp
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
            ref.child(str(ctx.author.id)).set(t_list)
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

@client.command()
async def balance(ctx):
    await open_account(ctx.author)
    users = await get_jar_data()

    karman = users[str(ctx.author.id)]["монетки"]

    embed = discord.Embed(title=f'Карман Игрока {ctx.author.display_name}', colour=discord.Colour(int('5BC1FF', 16)))
    embed.add_field(name = 'Монетки', value = karman)
    await ctx.send(embed = embed)


async def open_account(user):
    users = await get_jar_data()

    if str(user.id) in users:
        return False
    else:
        users[str(user.id)] = {}
        users[str(user.id)]["монетки"] = 0
    
    with open('moneyjar.json', 'w') as f:
        json.dump(users, f)

    return True


async def get_jar_data():
    with open('moneyjar.json', 'r') as f:
        users = json.load(f)
    return users



@client.command()
async def zapor(ctx, username):
    # Use the 'users' collection in your Cloud Firestore database
    user_ref = db.collection('users').document(username)
    # Store user data in a dictionary
    user_data = {
        'name': username,
        'guild': ctx.guild.id
    }
    # Set the user data in the document
    user_ref.set(user_data)
    await ctx.send(f"User {username} registered!")




client.run(os.environ['BOT_TOKEN'])
