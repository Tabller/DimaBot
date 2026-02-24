import itertools
import math
import time
from datetime import datetime
import discord
import asyncio
import os
import random
from discord import Color, Guild, Interaction
from discord.ext.commands import has_any_role
from discord.ui import Select
from discord.ext import commands, tasks
from dotenv import load_dotenv


from src.cogs.moderation_cog import finish_timeout_after
from src.config import nights_ref, economy_ref, inventory_ref, penalty_ref, servers_ref, PREFIX, WELCOME_MESSAGE_EN, \
    all_items, fish_book, cool_dict, all_fish, full_items, ui_localization, rpg_stuff_ref

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
    user.set({"item": "None",
              'start_time': '0',
              'end_time': "1",
              'guild_id': 'SERVER_ID1'})
elif servers_ref.get() is None:
    server = servers_ref.child("SERVER_ID")
    server.set({'PREFIX': f'{PREFIX}',
                'TIMEOUT_CHANNEL_ID': 'None',
                'TIMEOUT_ROLE_ID': 'None',
                'BOT_CHANNEL_ID': 'None',
                'LANGUAGE': 'RU'})
elif rpg_stuff_ref.get() is None:
    user = rpg_stuff_ref.child("USER_ID1")
    user.set({"current_quest": None,
              "current_lore": None
    })
else:
    pass

"""
Инициализация бота
"""

load_dotenv(dotenv_path='/root/DimaBot/.env')

intents = discord.Intents.all()
intents.message_content = True
async def restore_active_timeouts(bot):
    all_timeouts = penalty_ref.get() or {}

    for user_id, timeout_data in all_timeouts.items():
        current_time = datetime.now().timestamp()
        end_time = timeout_data.get('end_time', 0)

        if int(end_time) > int(current_time):
            remaining_time = int(end_time) - int(current_time)

            asyncio.create_task(
                finish_timeout_after(
                    bot=bot,
                    user_id=user_id,
                    guild_id=timeout_data['guild_id'],
                    remaining_time=remaining_time
                )
            )

            print(f"Resumed timeout for {user_id}")
        else:
            if user_id != 'USER_ID1':
                await finish_timeout_after(bot, user_id, timeout_data['guild_id'], 0)
                print(f"Deleted timeout for {user_id}")


async def get_prefix(bot, message):
    if not message.guild:
        return commands.when_mentioned_or("!")(bot, message)


    prefix = await asyncio.wait_for(
        asyncio.to_thread(lambda: str(servers_ref.child(str(message.guild.id)).child("PREFIX").get())
    ),
    timeout=5.0
    )


    if prefix is None or prefix == '':
        return commands.when_mentioned_or("!")(bot, message)
    return commands.when_mentioned_or(prefix)(bot, message)

client = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

async def load_extensions(bot: commands.Bot):
    extensions = ['src.cogs.moderation_cog',
                  'src.cogs.gamenight_cog',
                  'src.cogs.rpg_cog',
                  'src.cogs.other_cog',
                  'src.cogs.minigames_cog']

    for extension in extensions:
        try:
            await bot.load_extension(extension)
            print(f"Loaded {extension}")
        except Exception as e:
            print(f"Failed to load {extension}: {e}")


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
    client.loop.create_task(restore_active_timeouts(client))

    try:
        await load_extensions(client)
        synced = await client.tree.sync()
        print(f'Synced {len(synced)} interaction command(s).')
    except Exception as exception:
        print(f"event.on_ready: {exception}")

    if not presence_loop.is_running():
        presence_loop.start()



@client.event
async def on_guild_join(guild: Guild):
    servers_data = servers_ref.get()
    if not (str(guild.id) in servers_data):
        guild_server = servers_ref.child(str(guild.id))
        guild_server.set({'PREFIX': f'{PREFIX}', # Префикс бота.
                    'TIMEOUT_CHANNEL_ID': 'None', # ID канала для отправки в таймаут.
                    'TIMEOUT_ROLE_ID': 'None', # ID роли, которая выдаётся при таймауте.
                    'BOT_CHANNEL_ID': 'None', # ID технического канала, куда будут присылаться некоторые сообщения от бота (если это необходимо)
                    'LANGUAGE': 'RU'}) # LOCALIZATION LANGUAGE
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
"""
Shop
"""

@client.hybrid_command()
@commands.cooldown(1, 3, commands.BucketType.user)
async def shop(ctx):
    embed = myshop.shop_view(ctx.guild.id)


    class BackButton(discord.ui.View):
        def __init__(self, author, timeout=None):
            super().__init__(timeout=timeout)
            self.author = author

        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"

        @discord.ui.button(label=f'{ui_localization.get("shop").get("Back_Button").get(LANG)}', style=discord.ButtonStyle.success)
        async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(embed=myshop.shop_view(interaction.guild_id), view=shopButtons(ctx.author, timeout=None))

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

        @discord.ui.button(label=f'{ui_localization.get("shop").get("Buy_Button").get(LANG)}', style=discord.ButtonStyle.success)
        async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
            LANG = f"LANG_{servers_ref.child(str(interaction.guild_id)).child("LANGUAGE").get()}"
            embed = discord.Embed(color=Color.dark_purple(), title=f"{ui_localization.get("shop").get("Shop_Name").get(LANG)}", description=f"{ui_localization.get("shop").get("Buy_Interaction").get(LANG)} {current_emoji}")
            user_data = inventory_ref.child(str(self.author.id)).get()

            shop_price = full_items.get(current_emoji).get('shop_price')

            economy_data = economy_ref.child(str(self.author.id)).get()
            if economy_data is None:
                embed = discord.Embed(color=Color.dark_purple(), title=f"{ui_localization.get("shop").get("Shop_Name").get(LANG)}",
                                      description=f"{ui_localization.get("shop").get("Money_Warn").get(LANG)}")
                await interaction.response.edit_message(embed=embed, view=None)
                return
            else:
                current_coins = economy_data['coins']
                if int(current_coins) < int(shop_price):
                    embed = discord.Embed(color=Color.dark_purple(), title=f"{ui_localization.get("shop").get("Shop_Name").get(LANG)}",
                                          description=f"{ui_localization.get("shop").get("Money_Warn").get(LANG)}")
                    await interaction.response.edit_message(embed=embed, view=None)
                    return


            if user_data is None:
                if current_emoji in fish_book.keys():
                    multiplier_price = full_items.get(current_emoji)['multiplier_price']()
                    inventory_ref.child(str(self.author.id)).child(f'{current_emoji}' + str(int(time.time() * 1000))).set({
                      "price": int(shop_price) - int(random.randint(5, 15)),
                      "multiplier": multiplier_price,
                      "rarity": math.floor(multiplier_price)
                    })
                    current_coins = economy_data['coins']
                    economy_ref.child(str(self.author.id)).set({
                        'coins': current_coins - int(shop_price)
                    })
                    await interaction.response.edit_message(embed=embed, view=None)
                else:
                    item_key = f'{current_emoji}' + str(int(time.time() * 1000))
                    base_price = round(int(shop_price) * random.random(), 5)
                    multiplier_price = full_items.get(current_emoji)['multiplier_price']()
                    # inventory_ref.child(str(self.author.id)).update({f'{current_emoji}' + str(int(time.time() * 1000)): round(int(shop_price) * random.random(), 5)})
                    inventory_ref.child(str(self.author.id)).child(item_key).update(
                        {
                            "price": base_price,
                            "multiplier": multiplier_price,
                            "rarity": math.floor(multiplier_price)
                        }
                    )
                    current_coins = economy_data['coins']
                    economy_ref.child(str(self.author.id)).set({
                        'coins': current_coins - int(shop_price)
                    })
                    await interaction.response.edit_message(embed=embed, view=None)
            else:
                if current_emoji in fish_book.keys():
                    # inventory_ref.child(str(self.author.id)).update(
                    #     {f'{current_emoji}' + str(int(time.time() * 1000)): (int(shop_price) - int(random.randint(5, 15)))})
                    item_key = f'{current_emoji}' + str(int(time.time() * 1000))
                    base_price = int(shop_price) - int(random.randint(5, 15))
                    multiplier_price = full_items.get(current_emoji)['multiplier_price']()
                    inventory_ref.child(str(self.author.id)).child(item_key).update({
                        "price": base_price,
                        "multiplier": multiplier_price,
                        "rarity": math.floor(multiplier_price)
                    })

                    current_coins = economy_data['coins']
                    economy_ref.child(str(self.author.id)).set({
                        'coins': current_coins - int(shop_price)
                    })
                    await interaction.response.edit_message(embed=embed, view=None)
                else:
                    item_key = f'{current_emoji}' + str(int(time.time() * 1000))
                    base_price = int(int(shop_price) * random.random())
                    multiplier_price = full_items.get(current_emoji)['multiplier_price']()
                    # new_item = inventory_ref.child(str(self.author.id)).update({
                    #     f'{current_emoji}' + str(int(time.time() * 1000)): int(int(shop_price) * random.random())
                    # })
                    inventory_ref.child(str(self.author.id)).child(item_key).update({
                        "price": base_price,
                        "multiplier": multiplier_price,
                        "rarity": math.floor(multiplier_price)
                    })
                    current_coins = economy_data['coins']
                    economy_ref.child(str(self.author.id)).set({
                        'coins': current_coins - int(shop_price)
                    })
                    await interaction.response.edit_message(embed=embed, view=None)

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

    class shopButtons(discord.ui.View):
        def __init__(self, author, timeout=None):
            super().__init__(timeout=timeout)
            self.author = author

        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji=str(myshop.chosen_keys[0]))
        async def first(self, interaction: discord.Interaction, button: discord.ui.Button):
            global current_emoji
            LANG = f"LANG_{servers_ref.child(str(interaction.guild_id)).child("LANGUAGE").get()}"
            current_emoji = myshop.chosen_keys[0]
            item_info = discord.Embed(color=Color.dark_purple(), title=myshop.chosen_keys[0], description=None)
            item_info.add_field(name=f"{ui_localization.get("shop").get("Description_Label").get(LANG)}:", value=full_items.get(myshop.chosen_keys[0]).get("description").get(LANG), inline=True)
            await interaction.response.edit_message(embed=item_info, view=BackButton(ctx.author, timeout=None))

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji=str(myshop.chosen_keys[1]))
        async def second(self, interaction: discord.Interaction, button: discord.ui.Button):
            global current_emoji
            LANG = f"LANG_{servers_ref.child(str(interaction.guild_id)).child("LANGUAGE").get()}"
            current_emoji = myshop.chosen_keys[1]
            item_info = discord.Embed(color=Color.dark_purple(),
                                      title=myshop.chosen_keys[1],
                                      description=None)
            item_info.add_field(name=f"{ui_localization.get("shop").get("Description_Label").get(LANG)}:", value=full_items.get(myshop.chosen_keys[1]).get("description").get(
                LANG), inline=True)
            await interaction.response.edit_message(embed=item_info, view=BackButton(ctx.author, timeout=None))

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

        @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji=str(myshop.chosen_keys[2]))
        async def third(self, interaction: discord.Interaction, button: discord.ui.Button):
            global current_emoji
            current_emoji = myshop.chosen_keys[2]
            LANG = f"LANG_{servers_ref.child(str(interaction.guild_id)).child("LANGUAGE").get()}"
            item_info = discord.Embed(color=Color.dark_purple(),
                                      title=myshop.chosen_keys[2],
                                      description=None)
            item_info.add_field(name=f"{ui_localization.get("shop").get("Description_Label").get(LANG)}:", value=full_items.get(myshop.chosen_keys[2]).get("description").get(
                LANG), inline=True)
            await interaction.response.edit_message(embed=item_info, view=BackButton(ctx.author, timeout=None))

        async def interaction_check(self, interaction: Interaction):
            return interaction.user.id == self.author.id

    msg = await ctx.send(embed = embed, view=shopButtons(ctx.author, timeout=None))
    await task
    embed = discord.Embed(title="Магазин закрыт на обнову",
                               description="Введите ещё раз команду !shop для обновления магазина")
    await msg.edit(embed=embed, view=None)

'''
Функции
'''

async def get_user(user_cool_id):
    if not user_cool_id in cool_dict:
        try:
            user = await client.fetch_user(int(user_cool_id))
            cool_dict[user_cool_id] = user.display_name
        except discord.NotFound:
            cool_dict[user_cool_id] = user_cool_id
    return cool_dict[user_cool_id]

async def periodic_task():
    global shop_items
    global task
    while True:
        shop_items = myshop.initialize_shop()
        print("Shop changed")
        task = asyncio.create_task(shop_func())
        await task

async def shop_func():
    await asyncio.sleep(21600)


async def shop_Changed(ctx: discord.ext.commands.Context, msg: discord.Message):
    pass

class ShopClass():
    def __init__(self):
        self.embed = discord.Embed(color=Color.dark_purple(), title="Магазин", description=None)

        self.chosen_keys = []


    def initialize_shop(self):
        self.embed = discord.Embed(color=Color.dark_purple(), title="Магазин", description=None)
        self.chosen_keys = []

        shop_catalogue = list(full_items.keys())

        LANG = "LANG_RU"
        for _ in range(3):
            self.chosen_keys.append(random.choice(shop_catalogue))

        for i in self.chosen_keys:

            if self.chosen_keys.count(i) > 1:
                save_index = i
                while self.chosen_keys.count(save_index) != 1:
                    self.chosen_keys.remove(save_index)
                    self.chosen_keys.insert(self.chosen_keys.index(save_index),random.choice(shop_catalogue))

        for item in self.chosen_keys:
            self.embed.add_field(name=item, value=full_items.get(item).get("item_name").get(LANG), inline=True)
            self.embed.add_field(name=f"{full_items.get(item).get("shop_price")}", value="\n", inline=False)


        return self.chosen_keys

    def shop_view(self, guild_id):
        LANG = f"LANG_{servers_ref.child(str(guild_id)).child("LANGUAGE").get()}"
        self.embed = discord.Embed(color=Color.dark_purple(), title=f"{ui_localization.get("shop").get("Shop_Name").get(LANG)}")
        for item in self.chosen_keys:
            self.embed.add_field(name=item, value=full_items.get(item).get("item_name").get(LANG), inline=True)
            self.embed.add_field(name=f"{full_items.get(item).get("shop_price")}", value="\n", inline=False)
        return self.embed

'''
LeaderBoard
'''
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

myshop = ShopClass()

client.run(os.environ['BOT_TOKEN'])
