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
from discord import Webhook, SyncWebhook, Interaction
import aiohttp
import random
import json
import time
from dotenv import load_dotenv
import os

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

    embed = discord.Embed(title='димабот ft. Томатские Угодья',
                          description='Здесь находится вся актуальная информация о ссылках, которые ведут на томата.',
                          colour=discord.Colour(int('a970ff', 16)))
    embed.add_field(name='Команды димы',
                    value='\n`/submit [игра]` — Предложить игру для стрима в канал <#1185909058910310420> \n`/list` — Посмотреть список предложенных игр. \n`!balance` — Проверить свой карман (на наличие денег). \n`!fish` — Рыбалка симулятор. \n я амогус это проверка',
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

@client.command()
async def balance(ctx):
    user_data = economy_ref.child(str(ctx.author.id)).get()

    karman = user_data['coins']

    embed = discord.Embed(title=f'Карман Игрока {ctx.author.display_name}', colour=discord.Colour(int('5BC1FF', 16)))
    embed.add_field(name = 'Монетки', value = karman)
    await ctx.send(embed = embed)

@client.command()
@commands.cooldown(1, 6, commands.BucketType.user)
async def fish(ctx):
    user_data = economy_ref.child(str(ctx.author.id)).get()

    if user_data is None:
        economy_ref.child(ctx.author.id).set({'coins': 0})

    # global game_run

    game_run = True

    map_one_coordinates = [["◼️", "◼️", "◼️", "◼️", "◼️", "☀️", "◼️"],
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
    global previous_hook
    global previous_boat
    previous_hook = [4, 3]
    previous_boat = [2, 3]

    def map_print():
        # map_one_coordinates, fish_coord = spawn_fish()
        global line
        count = 0
        line = ''
        for row in map_one_coordinates:
            for emoji in row:
                if count < 7:

                    line = line + f''.join(emoji)
                    count += 1
                else:
                    line = line + f''.join('\n')
                    line = line + f''.join(emoji)
                    count = 1
        return line

    def move_boat(x,y, new_x):
        global raw_map
        raw_map = map_one_coordinates
        what_to_change = map_one_coordinates[y][x+new_x]
        raw_map[y][x + new_x] = "🛶"
        raw_map[y][x] = what_to_change
        previous_boat[1] += new_x
        return raw_map

    def spawn_fish():
        choice_x = [0, 6]
        choice_y = [5, 8]
        fish_emojis = ['🐟', '🐠', '🐡', '🪼']
        global raw_map
        raw_map = map_one_coordinates
        fish_y = random.choice(choice_y)
        fish_x = random.choice(choice_x)
        fish_coords = [fish_y, fish_x]
        raw_map[fish_y][fish_x] = random.choice(fish_emojis)

        print(raw_map, fish_coords)
        return raw_map, fish_coords

    spawn_fish()

    def change_coord(x, y, new_x, new_y):
        # if previous_hook[0] > 3 or new_y == -1:
        # global game_run
        global raw_map
        what_to_change = map_one_coordinates[y+new_y][x+new_x]
        if (what_to_change != "🟨") and (what_to_change != "🪸") and (what_to_change != "◼️") and (what_to_change != "🛶") and (what_to_change != '🐟') and (what_to_change != '🐠') and (what_to_change != '🐡') and (what_to_change != '🪼'):
            raw_map = move_boat(previous_boat[1], previous_boat[0], new_x)
            # raw_map = map_one_coordinates
            raw_map[y+new_y][x+new_x] = "🪝"
            raw_map[y][x] = what_to_change
            previous_hook[0] += new_y
            previous_hook[1] += new_x
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

            if what_to_change == '🐟':
                cm = random.randint(1, 100)
                line = f'вы поймали карася размером {cm} сантиметров'
                # base 5 * cm / 10
                current_coins = user_data.get('coins', 0)
                new_coins = current_coins + 5 * (cm / 10)
                economy_ref.child(str(ctx.author.id)).update({'coins': new_coins})

                game_run = False
                return line
            if what_to_change == '🐠':
                cm = random.randint(1, 100)
                line = f'вы поймали брата карася размером {cm} сантиметров'
                # base 6 * cm / 10
                current_coins = user_data.get('coins', 0)
                new_coins = current_coins + 6 * (cm / 10)
                economy_ref.child(str(ctx.author.id)).update({'coins': new_coins})

                game_run = False
                return line
            if what_to_change == '🐡':
                cm = random.randint(1, 100)
                line = f'вы поймали рыбу агу ага размером {cm} сантиметров'
                # base 8 * cm / 10
                current_coins = user_data.get('coins', 0)
                new_coins = current_coins + 8 * (cm / 10)
                economy_ref.child(str(ctx.author.id)).update({'coins': new_coins})

                game_run = False
                return line
            if what_to_change == '🪼':
                cm = random.randint(1, 100)
                line = f'вы поймали медузу крутую размером {cm} сантиметров'
                # base 10 * cm / 10
                current_coins = user_data.get('coins', 0)
                new_coins = current_coins + 10 * (cm/10)
                economy_ref.child(str(ctx.author.id)).update({'coins': new_coins})

                game_run = False
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

    class Buttons(discord.ui.View):
        def __init__(self, author, timeout=None):
            super().__init__(timeout=timeout)
            self.author = author

        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji='⬆️')
        async def up(self, interaction: discord.Interaction, button: discord.ui.Button):

            desc = change_coord(previous_hook[1], previous_hook[0], 0, -1)
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
            desc = change_coord(previous_hook[1], previous_hook[0], 0, 1)
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
            desc = change_coord(previous_hook[1], previous_hook[0], -1, 0)
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
            desc = change_coord(previous_hook[1], previous_hook[0], 1, 0)
            new_embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)),
                                      title=f'фишинг {ctx.author.display_name}', description=desc)
            if "🟦" in new_embed.description:
                await message.edit(embed=new_embed, view=Buttons(ctx.author, timeout=None))
            else:
                await message.edit(embed=new_embed, view=None)
            await interaction.response.defer()

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id


    embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)), title=f'фишинг {ctx.author.display_name}', description=map_print())
    if "вы" in embed.description:
        message = await ctx.send(embed=embed, view=None)
        await message.edit(embed=embed, view=None)
    else:
        message = await ctx.send(embed=embed, view=Buttons(ctx.author, timeout=None))
# d

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
client.run(os.environ['BOT_TOKEN'])
