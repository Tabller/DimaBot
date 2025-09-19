
import asyncio
import copy
import random
import re
import time

import discord
from discord import Interaction

from discord.ext import commands
from firebase_admin import db

from src.config import inventory_ref, economy_ref, items, active_games, maps, fish_available, fish_book, crafting_dict, \
    servers_ref, penalty_ref


class RPGCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    '''
    Секция с типичными командами использования
    '''

    # Инвертирует игровое поле рыбной мини-игры
    async def id0use(self, ctx, item):
        try:
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

            dictionary = inventory_data or {}


            global cool_item_name

            what_to_delete = {}
            for item_name, quantity in dictionary.items():
                if '👢' in item_name:
                    if not ('📌' in item_name):
                        what_to_delete[item_name] = quantity
                        cool_item_name = copy.deepcopy(item_name)
            pattern = r'[0-9]'
            new_string = re.sub(pattern, '', item)

            first_way = items.get(item)
            if first_way:
                inventory_path = f"{user_id}/{cool_item_name}"
                inventory_ref.child(inventory_path).delete()
            else:
                for key, val in what_to_delete.items():
                    if str(item) == str(val) or str(key) == str(item):
                        inventory_path = f"{user_id}/{key}"
                        inventory_ref.child(inventory_path).delete()
                        break

            embed = discord.Embed(title=f'Карман Игрока {ctx.author.display_name}',
                                  colour=discord.Colour(int('5BC1FF', 16)))
            embed.add_field(name=f"",
                            value=f"Вы надели себе на голову 👢. Что-то поменялось, но вы не можете сказать, что именно...")

            await ctx.send(embed=embed)
        except Exception as e:
            print(f"rpg_cog.id0use: {e}")
            await ctx.send("аа чё то пошло не по плану...")

    async def id26use(self, ctx):
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
            response = await self.client.wait_for('message', check=check, timeout=30)

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

    @commands.hybrid_command(name="info", with_app_command=True)
    async def info(self,ctx, *, item: str):
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
                    response = await self.client.wait_for('message', check=check, timeout=30)

                    selected_item = response.content
                else:
                    selected_item = new_string

                for key, value in available_items.items():
                    if str(value) == selected_item or str(key) == selected_item or len(available_items) == 1:
                        cleaned_text = re.sub(r'^[^\d]*', '', key)

                        embed = discord.Embed(title=f'Карман Игрока {ctx.author.display_name}',
                                              colour=discord.Colour(int('5BC1FF', 16)))
                        embed.add_field(name=new_string,
                                        value=f"{name}, предмет получен <t:{str(int(cleaned_text) // 1000)}:F>")
                        embed.add_field(name="Описание:", value=description)
                        await ctx.send(embed=embed)



            except asyncio.TimeoutError:
                await ctx.send("ты чет призадумался, попробуй лучше снова")
        else:
            await ctx.send(f"хрень, такого предмета нету")

    @commands.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def pin(self, ctx, *, item: str):
        pattern = r'[0-9\s]'
        new_item = re.sub(pattern, '', item)
        user_id = ctx.author.id
        inventory_data = inventory_ref.child(str(user_id)).get()

        if inventory_data is None:
            await ctx.send('xnj ты собрался пригвоздить')

        dictionary = {}
        for item_name, quantity in inventory_data.items():
            if '📌' in new_item:
                if not ('📌' in item_name):
                    continue
                else:
                    dictionary[item_name] = quantity
            else:
                if '📌' in item_name:
                    continue
                else:
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
                    f"выбери, какой из нескольких '{item}' пригвоздить/отгвоздить (укажи индекс):\n" +
                    "\n".join([f"{index + 1}. {new_string}: {value} {word}" for index, name, value in items_to_pin])
                )

                def check(m):
                    return m.author == ctx.author and m.content.isdigit() and 0 <= int(m.content) - 1 < len(
                        items_to_pin) or m.content == "всё"

            try:
                if len(what_to_pin) > 1 and item != "inventory" and item != "всё":
                    response = await self.client.wait_for('message', check=check, timeout=30)
                    if response.content != 'inventory' and response.content != 'всё':
                        index, name, value = items_to_pin[int(response.content) - 1]
                        await ctx.send(f"окей, ща я подумаю чё делать с... {index + 1}. {item}: {value} {word}")
                        selected_item = int(response.content) - 1

                    else:
                        selected_item = "всё"
                else:
                    selected_item = "всё"

                funny_copy_what_to_pin = copy.deepcopy(what_to_pin)

                for index, (name, value) in enumerate(what_to_pin.items()):
                    if selected_item == int(index) or selected_item == "всё":
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
                        pass

            except asyncio.TimeoutError:
                await ctx.send("ты чет призадумался, попробуй лучше снова")
        else:
            await ctx.send(f"хрень, такого предмета у тебя нету")

    @commands.command()
    @commands.cooldown(3, 1, commands.BucketType.user)
    async def use(self, ctx, *, item: str):
        user_id = ctx.author.id
        inventory_data = inventory_ref.child(str(user_id)).get()
        if inventory_data is None:
            await ctx.send('ты сон у тебя нет предметов')
            return

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

        if len(available_items) == 0:
            await ctx.send(f"хрень, такого предмета нету")
            return

        if len(available_items) > 1 and item != "inventory":
            await ctx.send(
                f"у тебя несколько '{item}'. выбери конкретный предмет, чтобы использовать предмет\n"
                + "\n".join([f"- {name}: {value} {word}" for name, value in available_items.items()])
            )

            def check(m):
                return m.author == ctx.author

            try:
                response = await self.client.wait_for('message', check=check, timeout=30)
                selected_item = response.content
            except asyncio.TimeoutError:
                await ctx.send("ты чет призадумался, попробуй лучше снова")
                return
        else:
            selected_item = item


        if func is not None:
            if new_string == '👢':
                await self.id0use(ctx, selected_item)
            elif new_string == '⛵':
                await self.id26use(ctx)
            else:
                await ctx.send("Этот предмет не имеет никакого применения...")

    @commands.command()
    @commands.cooldown(1, 6, commands.BucketType.user)
    async def fish(self, ctx):
        user_id = ctx.author.id
        if user_id in active_games:
            await ctx.send(f"ты уже смешарик, доиграй сначала")
            return

        active_games[user_id] = True

        def double_chance():
            i = 1
            while True:
                if random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 1]):
                    i += 1
                else:
                    return i

        class FishGame():

            def __init__(self):
                user_data = economy_ref.child(str(ctx.author.id)).get()
                ref = db.reference(f'inventory/{user_id}/fishing_location')
                try:
                    self.word = str(ref.get())
                    map_coordinates, description, fish_quantity, hook_coordinates, boat_coordinates, placeholder1, placeholder2 = maps.get(
                        self.word)
                except:
                    self.word = "спокойный океан"
                    map_coordinates, description, fish_quantity, hook_coordinates, boat_coordinates, placeholder1, placeholder2 = maps.get(
                        self.word)

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

                for _ in range(boot_count * 2 % 4):
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
                what_to_change = self.location_coordinates[y][x + new_x]
                raw_map[y][x + new_x] = "🛶"
                raw_map[y][x] = what_to_change
                self.previous_boat[1] += new_x
                return raw_map

            def spawn_fish(self):

                choice_x = [0, 6]
                choice_y = [5, 8]
                inventory_data = inventory_ref.child(str(ctx.author.id)).get()



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

                global raw_map
                what_to_change = self.location_coordinates[y + new_y][x + new_x]
                if (what_to_change != "🟨") and (what_to_change != "🪸") and (what_to_change != "◼️") and (
                        what_to_change != "🛶") and (what_to_change != "🟫") and (what_to_change != "🟧") and (
                        what_to_change != "🌆") and (what_to_change != "🌇") and (what_to_change != "⚙️") and (
                not (what_to_change in fish_book.keys())):
                    raw_map = self.move_boat(self.previous_boat[1], self.previous_boat[0], new_x)
                    # raw_map = map_one_coordinates
                    raw_map[y + new_y][x + new_x] = "🪝"
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


                    if what_to_change in fish_book.keys():
                        line, multiplier, typeof = fish_book.get(what_to_change)
                        line = line.format(self.cm)
                        inventory_data = inventory_ref.child(str(ctx.author.id)).get()

                        if inventory_data is None:
                            if typeof == "fish":
                                inventory_ref.child(str(ctx.author.id)).set(
                                    {what_to_change + str(int(time.time() * 1000)): self.cm * multiplier})
                            else:
                                inventory_ref.child(str(ctx.author.id)).set(
                                    {what_to_change + str(int(time.time() * 1000)): 1 * multiplier})
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
                new_embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)),
                                          title=f'фишинг {ctx.author.display_name}', description=desc)
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
                new_embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)),
                                          title=f'фишинг {ctx.author.display_name}', description=desc)
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

        embed = discord.Embed(colour=discord.Colour(int('5BC1FF', 16)), title=f'фишинг {ctx.author.display_name}',
                              description=game_up.map_print())
        if "вы" in embed.description:
            message = await ctx.send(embed=embed, view=None)
            await message.edit(embed=embed, view=None)
        else:
            message = await ctx.send(embed=embed, view=Buttons(ctx.author, timeout=None))

        while game_up.game_run:
            await asyncio.sleep(1)

    @commands.hybrid_command()
    async def sell(self, ctx, item: str):
        """Команда для продажи вещи/вещей/всего инвентаря"""
        user_id = ctx.author.id
        inventory_data = inventory_ref.child(str(user_id)).get()

        if inventory_data is None:
            await ctx.send('тебе нечего продать на файерградском рынке')

        dictionary = {}
        for item_name, quantity in inventory_data.items():
            if not ('effects' in item_name):
                dictionary[item_name] = quantity

        # здесь изменение

        what_to_sell = {}
        for item_name, quantity in dictionary.items():
            if item in item_name or item == "inventory":
                if not ('📌' in item_name) and not ('effects' in item_name):
                    what_to_sell[item_name] = quantity

        pattern = r'[0-9]'
        new_string = re.sub(pattern, '', item)

        definitely_to_sell = []
        for index, (name, value) in enumerate(what_to_sell.items()):
            definitely_to_sell.append((index, name, value))

        if len(what_to_sell) >= 1:

            if len(what_to_sell) > 1 and item != "inventory":
                multiplier, word, name, way_to_sell, func, icon, price = items.get(new_string)

                await ctx.send(
                    f"ничего себе, у тебя несколько '{item}'. выбери чё продать из этого (укажи индекс):\n" +
                   # "\n".join([f"- {new_string}: {value} {word}" for name, value in what_to_sell.items()])
                "\n".join([f"{index + 1}. {new_string}: {value} {word}" for index, name, value in definitely_to_sell])
                )

                msg = await ctx.send('или напиши "всё" если хочешь продать всё сразу')

                def check(m):
                    return m.author == ctx.author and m.content.isdigit() and 0 <= int(m.content) - 1 < len(
                        definitely_to_sell) or m.content == "всё"

            try:
                if len(what_to_sell) > 1 and item != "inventory" and item != "всё":
                    response = await self.client.wait_for('message', check=check, timeout=30)

                    if response.content != "всё":
                        index, name, value = definitely_to_sell[int(response.content) - 1]
                        await ctx.send(f"окей, ща продадим {index + 1}. {item}: {value} {word}")
                        selected_item = int(response.content) - 1
                    else:
                        selected_item = "всё"

                else:
                    selected_item = "всё"

                funny_copy_what_to_sell = copy.deepcopy(what_to_sell)

                for index, (key, value) in enumerate(what_to_sell.items()):
                    if selected_item == int(index) or selected_item == "всё":
                        try:
                            inventory_path = f"{user_id}/{key}"
                            inventory_ref.child(inventory_path).delete()
                            user_economy_ref = economy_ref.child(str(user_id))
                            user_data = user_economy_ref.get()

                            if user_data is None:
                                user_economy_ref.set({"coins": 0})

                            if (new_string in key) or (new_string == 'inventory'):
                                if new_string == 'inventory':
                                    multiplier, word, name, way_to_sell, func, icon, price = items.get(
                                        re.sub(pattern, '', key))
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

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def craft(self, ctx, *, emoji):
        """Команда для крафта различных предметов"""

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

            if all(item in inventory and not ('📌' in item) for item in ingredients):
                for item in ingredients:
                    for item2 in inventory_with_timestamps:
                        if item in item2:
                            items_you_used.append(item)
                            inventory_path = f"{str(ctx.author.id)}/{str(item2)}"
                            inventory_ref.child(inventory_path).delete()
                            break

                if found_recipe:
                    new_item = inventory_ref.child(str(ctx.author.id)).update(
                        {found_recipe[5] + str(int(time.time() * 1000)): int(
                            int(int(found_recipe[6]) * random.random()) * int(found_recipe[0]))})
                    await ctx.send(f"ура, вы скрафтили {found_recipe[5]}")
                else:
                    new_item = inventory_ref.child(str(ctx.author.id)).update(
                        {'💩' + str(int(time.time() * 1000)): int(1)})
                    await ctx.send(f"ты намудрил с рецептом, и скрафтил {'💩'}.")
            else:

                # new_item = inventory_ref.child(str(ctx.author.id)).update(
                #    {'💩' + str(int(time.time() * 1000)): int(1)})
                if len(items_you_used) == 0:
                    await ctx.send(f'ну у тебя каких-то вещей нету в инвентаре')
                else:
                    await ctx.send(f"у вас не получилось скрафтить предмет.")
                for used_item in items_you_used:
                    if used_item in ingredients:
                        if len(ingredients) == 3:
                            await ctx.send(
                                f"возможно, этот предмет используется в крафте: {str(used_item)} + ??? + ???")
                        else:
                            await ctx.send(f"возможно, этот предмет используется в крафте: {str(used_item)} + ???")


        else:
            await ctx.send("ты че как бомжик аид, беги собирать вещи")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def почистить(self, ctx, emoji):
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
        current_penalty = int(penalty_data.get("item"))
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
                        penalty_ref.child(str(ctx.author.id)).update({"item": new_penalty})

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

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def profile(self, ctx, member: discord.Member = None):
        """Команда для открытия своего баланса и инвентаря"""
        user_data = (member and economy_ref.child(str(member.id)).get()) or economy_ref.child(str(ctx.author.id)).get()
        user_name = (member and member.display_name) or ctx.author.display_name
        inventory_data = (member and inventory_ref.child(str(member.id)).get()) or inventory_ref.child(
            str(ctx.author.id)).get() or {}

        if "player" in user_data:
            pass
        else:
            (member and economy_ref.child(str(member.id)).child("player").set("😃👔🖐👖")) or economy_ref.child(
                str(ctx.author.id)).child("player").set("😃👔🖐👖")
            user_data = (member and economy_ref.child(str(member.id)).get()) or economy_ref.child(
                str(ctx.author.id)).get()

        if "health" in user_data:
            pass
        else:
            (member and economy_ref.child(str(member.id)).child("health").set("5")) or economy_ref.child(
                str(ctx.author.id)).child("health").set("5")
            user_data = (member and economy_ref.child(str(member.id)).get()) or economy_ref.child(
                str(ctx.author.id)).get()

        coins = user_data['coins']
        character = user_data['player']
        health = user_data['health']

        character_embed = discord.Embed(title=f"Профиль Игрока {user_name}", colour=discord.Colour(int('5BC1FF', 16)))
        character_embed.add_field(
            name=f"⬛⬛{character[4] if len(character) > 4 else "⬛"}⬛⬛\n"
                 f"⬛⬛{character[0]}⬛⬛\n"
                 f"⬛{character[2]}{character[1]}{character[2]}️⬛\n"
                 f"⬛{character[5] if len(character) > 4 else "⬛"}{character[3]}{character[4] if len(character) > 4 else "⬛"}⬛\n"
                 f"⬛⬛{character[6] if len(character) > 4 else "⬛"}⬛⬛\n",
            value=f"HP: {health}❤"
        )

        await ctx.send(embed=character_embed)

        def balance_sort(page: int, per_page: int = 10):

            embed = discord.Embed(title=f'Карман Игрока {user_name}', colour=discord.Colour(int('5BC1FF', 16)))
            embed.add_field(name='Монетки', value=coins)

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
                    multiplier, word, name, way_to_sell, func, icon, price = items.get(
                        new_string.replace('📌', '').strip())
                    embed.add_field(name=str(new_string), value=f'{quantity} {word}')

            if not (inventory_data == {}):
                embed.set_footer(
                    text=f"страница {page}/{(len(inventory_data.items()) + per_page - 1) // per_page}"
                )
            else:
                embed.set_footer(
                    text=f"страница {page}/1"
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

        await ctx.send(embed=embed, view=BalanceView())


async def setup(client):
    await client.add_cog(RPGCog(client))
