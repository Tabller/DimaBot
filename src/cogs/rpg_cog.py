
import asyncio
import copy
import math
import random
import re
import time
from copy import deepcopy

import discord
from attr.validators import disabled
from discord import Interaction
from discord import app_commands

from discord.ext import commands
from firebase_admin import db
from pathlib import Path
from src.config import inventory_ref, economy_ref, all_items, active_games, maps, fish_available, fish_book, \
    crafting_dict, \
    servers_ref, penalty_ref, all_fish, full_items, rarity_distribution, multiplier_distribution, speech_bubble, \
    rpg_stuff_ref, rpg_quest_items, ui_localization, locations, rpg_lore_quests

# in_dialogues = list()

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

            first_way = all_items.get(item)
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

    # async def id28use(self, interaction: discord.Interaction):
    #     user_id = interaction.user.id
    #     lore_data = rpg_stuff_ref.child(str(user_id)).get()
    #
    #     if lore_data is None:
    #         inventory_ref.child(str(user_id)).set({
    #         "current_quest": None,
    #         "current_lore": 1
    #      })
    #         print("norm")
    #     else:
    #         pass

    def quest_1(self):
        pass

    def universal_func(self, ctx, item: str):
        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"
        pattern = r'[0-9\s]'
        new_item = re.sub(pattern, '', item)
        user_id = ctx.author.id
        inventory_data = inventory_ref.child(str(user_id)).get()

        cases = {
            1: {

            }
        }

        if inventory_data is None:
            raise ValueError("Инвентарь пользователя не найден")

        
    @commands.hybrid_command(name="info", with_app_command=True)
    async def info(self,ctx, *, item: str):
        user_id = ctx.author.id
        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"
        inventory_data = inventory_ref.child(str(user_id)).get()

        if inventory_data is None:
            await ctx.send(f'{ui_localization.get("info").get("Info_No_Inventory").get(LANG)}')

        dictionary = {}
        for item_name, quantity in inventory_data.items():
            dictionary[item_name] = quantity

        available_items = {}
        for item_name, quantity in dictionary.items():
            if item in item_name or item == "inventory":
                available_items[item_name] = quantity
        pattern = r'[0-9]'
        new_string = re.sub(pattern, '', item)

        fullest_items = full_items | rpg_quest_items
        item_data = fullest_items[new_string]
        if new_string in all_fish.keys():
            word = "см" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("cm").get(LANG)}"
        else:
            word = "монет" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("coins").get(LANG)}"


        if len(available_items) >= 1:

            if len(available_items) > 1 and item != "inventory":
                await ctx.send(
                    f"{ui_localization.get("info").get("Info_Several_Items1").get(LANG)} '{item}'. {ui_localization.get("info").get("Info_Several_Items2").get(LANG)}\n{ui_localization.get("info").get("Info_Several_Items3").get(LANG)}:\n" +
                    "\n".join([f"- {name}: {value.get("price") if not isinstance(value, int) else value} {word}" for name, value in available_items.items()])
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
                    if str(value.get("price") if not isinstance(value, int) else value) == selected_item or str(key) == selected_item or len(available_items) == 1:
                        cleaned_text = re.sub(r'^[^\d]*', '', key)

                        temp_str = ""
                        multiplier_path = inventory_ref.child(str(ctx.author.id)).child(key).child('multiplier')
                        multiplier_price = multiplier_path.get()

                        for _ in multiplier_distribution.keys():
                            if multiplier_price is not None:
                                if eval(_.replace("value", str(multiplier_price))):
                                    temp_str += multiplier_distribution.get(_)
                        if temp_str == "":
                            temp_str = "🌞"




                        moon = temp_str
                        rarity = inventory_ref.child(str(ctx.author.id)).child(key).child('rarity').get()

                        if rarity is None:
                            rarity = 0
                        embed = discord.Embed(title=f'{ui_localization.get("profile").get("Profile_Title").get(LANG)} {ctx.author.display_name}',
                                              colour=discord.Colour(int('5BC1FF', 16)))
                        embed.add_field(name=new_string,
                                        value=f"{item_data["item_name"].get(LANG)}, {ui_localization.get("info").get("Info_Item_Obtained").get(LANG)} <t:{str(int(cleaned_text) // 1000)}:F>", inline=False)
                        embed.add_field(name=f"{ui_localization.get("shop").get("Description_Label").get(LANG)}:", value=f'```{item_data["description"].get(LANG)}```', inline=False)

                        if multiplier_price is not None:
                            embed.add_field(name=f"{ui_localization.get("info").get("Info_Moon_Blessing").get(LANG)}:", value=moon, inline=False)
                        embed.add_field(name=f"{ui_localization.get("info").get("Info_Rarity").get(LANG)}:", value=f"{rarity_distribution.get(int(rarity)).get(LANG)} {"⭐"*rarity if rarity is not None else ""}", inline=False)
                        await ctx.send(embed=embed)



            except asyncio.TimeoutError:
                await ctx.send(f"{ui_localization.get("info").get("AFK_Warn").get(LANG)}")
        else:
            await ctx.send(f"{ui_localization.get("info").get("WRONG_ITEM_Warn").get(LANG)}")

    @commands.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def pin(self, ctx, *, item: str):
        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"
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

        fullest_items = full_items | rpg_quest_items
        item_data = fullest_items[new_string.replace('📌', '')]

        if new_string in all_fish.keys():
            word = "см" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("cm").get(LANG)}"
        else:
            word = "монет" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("coins").get(LANG)}"

        if len(what_to_pin) >= 1:

            if len(what_to_pin) > 1 and item != "inventory":

                items_to_pin = []
                for index, (name, value) in enumerate(what_to_pin.items()):
                    items_to_pin.append((index, name, value))


                await ctx.send(
                    f"выбери, какой из нескольких '{item}' пригвоздить/отгвоздить (укажи индекс):\n" +
                    "\n".join([f"{index + 1}. {new_string}: {value.get("price") if not isinstance(value, int) else value} {word}" for index, name, value in items_to_pin])
                )

                def check(m):
                    return m.author == ctx.author and m.content.isdigit() and 0 <= int(m.content) - 1 < len(
                        items_to_pin) or m.content == "всё" or m.content == "all"

            try:
                if len(what_to_pin) > 1 and item != "inventory" and item != "всё" and item != "all":
                    response = await self.client.wait_for('message', check=check, timeout=30)

                    if response.content != 'inventory' and response.content != 'всё':
                        index, name, value = items_to_pin[int(response.content) - 1]

                        try:
                            price = value.get("price") if value.get("price") is not None else value
                        except:
                            price = value

                        await ctx.send(f"окей, ща я подумаю чё делать с... {index + 1}. {item}: {price} {word}")
                        selected_item = int(response.content) - 1

                    else:
                        selected_item = "всё"
                else:
                    selected_item = "всё"

                funny_copy_what_to_pin = copy.deepcopy(what_to_pin)



                for index, (name, value) in enumerate(what_to_pin.items()):
                    try:
                        price = value.get("price") if value.get("price") is not None else value
                    except:
                        price = value
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
                                    await ctx.send(f"вы пригвоздили {new_string}: {price} {word}")
                                else:
                                    inventory_ref.child(inventory_path).delete()
                                    inventory_ref.child(str(ctx.author.id)).update({
                                        f'{name.replace('📌', '').strip()}': value
                                    })
                                    await ctx.send(f"вы отгвоздили {new_string}: {price} {word}")

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
        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"
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

        fullest_items = full_items | rpg_quest_items

        item_name, multiplier_price, description, usage, shop_price = fullest_items.get(new_string)

        if new_string in all_fish.keys():
            word = "см" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("cm").get(LANG)}"
        else:
            word = "монет" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("coins").get(LANG)}"

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


        if usage is not None:
            if new_string == '👢':
                await self.id0use(ctx, selected_item)
            elif new_string == '⛵':
                await self.id26use(ctx)
            elif new_string == '🫖':
                await self.id28use(ctx)
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

                fish_emojis = deepcopy(no_fish_rod)


                if inventory_data is None:
                    pass
                else:
                    fish_rod_list = []
                    for key, value in inventory_data.items():
                        new_string = re.sub(r'[0-9]', '', key)
                        fish_rod_list.append(new_string)


                    if ('🎣' in fish_rod_list) or ('📌🎣' in fish_rod_list):
                        fish_emojis = deepcopy(level1_fish_rod)

                        if ('🫖' in fish_rod_list) or ('📌🫖' in fish_rod_list):
                            fish_emojis.remove('🫖')
                    if ('🫖' in fish_rod_list) or ('📌🫖' in fish_rod_list):
                        fish_emojis.remove('🫖')

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
                            item_key = what_to_change + str(int(time.time() * 1000))
                            if typeof == "fish":
                                inventory_ref.child(str(ctx.author.id)).child(item_key).set({
                                    "price": round(self.cm * multiplier(), 3),
                                    "multiplier": round(multiplier(), 9),
                                    "rarity": math.floor(round(multiplier(), 9))
                                })
                                # inventory_ref.child(str(ctx.author.id)).set(
                                #     {what_to_change + str(int(time.time() * 1000)): self.cm * multiplier})
                            else:
                                inventory_ref.child(str(ctx.author.id)).child(item_key).set({
                                    "price": round(1 * multiplier(), 3),
                                    "multiplier": round(multiplier(), 9),
                                    "rarity": math.floor(round(multiplier(), 9))
                                })
                                # inventory_ref.child(str(ctx.author.id)).set(
                                #     {what_to_change + str(int(time.time() * 1000)): 1 * multiplier})
                        else:
                            if typeof == "fish":
                                item_key = what_to_change + str(int(time.time() * 1000))
                                inventory_ref.child(str(ctx.author.id)).child(item_key).update({
                                    "price": round(self.cm * multiplier(), 3),
                                    "multiplier": round(multiplier(), 9),
                                    "rarity": math.floor(round(multiplier(), 9))
                                })
                            else:
                                item_key = what_to_change + str(int(time.time() * 1000))
                                inventory_ref.child(str(ctx.author.id)).child(item_key).set({
                                    "price": round(1 * multiplier(), 3),
                                    "multiplier": round(multiplier(), 9),
                                    "rarity": math.floor(round(multiplier(), 9))
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
        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"
        """Команда для продажи вещи/вещей/всего инвентаря"""
        user_id = ctx.author.id
        inventory_data = inventory_ref.child(str(user_id)).get()

        if inventory_data is None:
            await ctx.send(f'{ui_localization.get("sell").get("Sell_No_Inventory").get(LANG)}')

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
                if new_string in all_fish.keys():
                    word = "см" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("cm").get(LANG)}"
                else:
                    word = "монет" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("coins").get(LANG)}"

                await ctx.send(
                    f"{ui_localization.get("sell").get("Sell_Several_Item1").get(LANG)} '{item}'. {ui_localization.get("sell").get("Sell_Several_Item2").get(LANG)}:\n" +
                   # "\n".join([f"- {new_string}: {value} {word}" for name, value in what_to_sell.items()])
                "\n".join([f"{index + 1}. {new_string}: {value.get("price") if not isinstance(value, int) else value} {word}" for index, name, value in definitely_to_sell])
                )

                msg = await ctx.send(f'{ui_localization.get("sell").get("Sell_Several_Item3").get(LANG)}')

                def check(m):
                    return m.author == ctx.author and m.content.isdigit() and 0 <= int(m.content) - 1 < len(
                        definitely_to_sell) or m.content == "всё" or m.content == "all"

            try:
                if new_string in all_fish.keys():
                    word = "см" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("cm").get(LANG)}"
                else:
                    word = "монет" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("coins").get(LANG)}"

                if len(what_to_sell) > 1 and item != "inventory" and item != "всё" and item != "all":
                    response = await self.client.wait_for('message', check=check, timeout=30)

                    if response.content != "всё" and response.content != "all":
                        index, name, value = definitely_to_sell[int(response.content) - 1]
                        if isinstance(value, int):
                            await ctx.send(f"окей, ща продадим {index + 1}. {item}: {value} {word}")
                        else:
                            await ctx.send(f"{ui_localization.get("sell").get("Sell_Start").get(LANG)} {index + 1}. {item}: {value.get("price")} {word}")
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
                                if not isinstance(value, int):
                                    sell_price = int(int(value.get("price")) * value.get("multiplier") * random.random())
                                else:
                                    sell_price = int(value * random.uniform(1, 2))
                                current_coins = user_data.get("coins", 0)
                                user_economy_ref.update({"coins": current_coins + sell_price})

                                funny_copy_what_to_sell.pop(key)
                                if new_string == 'inventory':

                                    cool_string = str(re.sub(pattern, '', key))

                                    await ctx.send(f"{ui_localization.get("sell").get("Sell_Phrase1").get(LANG)} {cool_string} {ui_localization.get("sell").get("Sell_Phrase2").get(LANG)} {sell_price} {ui_localization.get("values").get("coin").get(LANG)}")
                                else:
                                    await ctx.send(f"{ui_localization.get("sell").get("Sell_Phrase1").get(LANG)} {new_string} {ui_localization.get("sell").get("Sell_Phrase2").get(LANG)} {sell_price} {ui_localization.get("values").get("coin").get(LANG)}")

                            if selected_item != "всё":
                                break
                            elif len(funny_copy_what_to_sell) == 0:
                                break
                        except Exception as e:
                            await ctx.send(f"{ui_localization.get("sell").get("Sell_Error").get(LANG)} {e}")
                    else:
                        print("говно переделывай")

                # inventory_ref.child(str(user_id)).child(item)
            except asyncio.TimeoutError:
                await ctx.send(f"{ui_localization.get("info").get("AFK_Warn").get(LANG)}")
        else:
            await ctx.send(f"{ui_localization.get("info").get("WRONG_ITEM_Warn").get(LANG)}")

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def craft(self, ctx, *, emoji):
        """Команда для крафта различных предметов"""
        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"
        ingredients = {
            emoji.strip()
            for emoji in emoji.split()
            if emoji.strip() and emoji.strip() != "️"
        }

        found_recipe = None
        icon = None
        for key in crafting_dict:
            if ingredients == key:
                found_recipe = crafting_dict.get(key)
                for i in full_items.keys():
                    if str(full_items.get(i).get('item_name').get(LANG)) == str(
                            crafting_dict.get(key).get('item_name').get(LANG)):
                        icon = i
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
                    f = lambda: 1 if random.random() > 0.65 else 0
                    total = 0
                    for i in range(8):
                        total += f()

                    multiplier_price = full_items.get(icon)['multiplier_price']()
                    new_item = inventory_ref.child(str(ctx.author.id)).update(
                        {icon + str(int(time.time() * 1000)): {
                            "multiplier": multiplier_price,
                            "price": round(int(full_items.get(icon)['shop_price'] + math.floor(multiplier_price)) * random.random(), 5),
                            "rarity": total
                        }})

                    await ctx.send(f"{ui_localization.get("craft").get("craft_success").get(LANG)} {icon}")
                else:
                    g = lambda: 1 if random.random() > 0.85 else 0
                    total = 0
                    for i in range(9):
                        total += g()

                    new_item = inventory_ref.child(str(ctx.author.id)).update(
                        {'💩' + str(int(time.time() * 1000)): {
                            "multiplier": round((random.random() + 1), 9),
                            "price": int(1),
                            "rarity": total
                        }})
                    await ctx.send(f"{ui_localization.get("craft").get("craft_fail1").get(LANG)} {'💩'}.")
            else:
                if len(items_you_used) == 0:
                    await ctx.send(f'{ui_localization.get("craft").get("craft_insufficient_items").get(LANG)}')
                else:
                    await ctx.send(f"{ui_localization.get("craft").get("craft_fail2").get(LANG)}")
                for used_item in items_you_used:
                    if used_item in ingredients:
                        if len(ingredients) == 3:
                            await ctx.send(
                                f"{ui_localization.get("craft").get("craft_possible_usage").get(LANG)}: {str(used_item)} + ??? + ???")
                        else:
                            await ctx.send(f"{ui_localization.get("craft").get("craft_possible_usage").get(LANG)}: {str(used_item)} + ???")


        else:
            await ctx.send(f"{ui_localization.get("craft").get("craft_no_inventory").get(LANG)}")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def peel(self, ctx, emoji):
        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"
        try:
            timeout_role_id = servers_ref.child(str(ctx.guild.id)).get().get("TIMEOUT_ROLE_ID")
        except:
            await ctx.send(f"{ui_localization.get("peel").get("peel_no_timeout_role").get(LANG)}")
            return

        if not timeout_role_id or not any(role.id == int(timeout_role_id) for role in ctx.author.roles):
            await ctx.send(f"{ui_localization.get("peel").get("peel_user_not_in_cage").get(LANG)}")
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
                    shop_price = full_items.get(emoji).get('shop_price')
                    base_price = round(int(shop_price) * random.random() * random.random(), 5)
                    multiplier_price = full_items.get(emoji)['multiplier_price']()
                    user_data = inventory_ref.child(user_id).get()
                    if user_data is None:
                        inventory_ref.child(user_id).set({'🍌' + str(int(time.time() * 1000)): {
                            "price": base_price,
                            "multiplier": multiplier_price,
                            "rarity": math.floor(multiplier_price)
                        }})
                    else:
                        new_banana = inventory_ref.child(user_id).update({
                            '🍌' + str(int(time.time() * 1000)): {
                            "price": base_price,
                            "multiplier": multiplier_price,
                            "rarity": math.floor(multiplier_price)
                        }})

                    if current_penalty > 0:
                        new_penalty = max(0, current_penalty - 1)
                        penalty_ref.child(str(ctx.author.id)).update({"item": new_penalty})

                        await ctx.reply(f"{ui_localization.get("peel").get("peel_quantity_left").get(LANG)} {new_penalty}")

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
                                    await ctx.send(f"{ui_localization.get("peel").get("peel_escape1").get(LANG)}, {member.mention} {ui_localization.get("peel").get("peel_escape2").get(LANG)}")
        else:
            await ctx.reply(f"{ui_localization.get("peel").get("peel_double_cage").get(LANG)}")

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def profile(self, ctx, member: discord.Member = None):
        """Команда для открытия своего баланса и инвентаря"""
        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"
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

        character_embed = discord.Embed(title=f"{ui_localization.get("profile").get("Profile_Title").get(LANG)} {user_name}", colour=discord.Colour(int('5BC1FF', 16)))
        character_embed.add_field(
            name=f"⬛⬛{character[4] if len(character) > 4 else "⬛"}⬛⬛\n"
                 f"⬛⬛{character[0]}⬛⬛\n"
                 f"⬛{character[2]}{character[1]}{character[2]}️⬛\n"
                 f"⬛{character[5] if len(character) > 4 else "⬛"}{character[3]}{character[4] if len(character) > 4 else "⬛"}⬛\n"
                 f"⬛⬛{character[6] if len(character) > 4 else "⬛"}⬛⬛\n",
            value=f"HP: {"❤" * int(health)}"
        )

        await ctx.send(embed=character_embed)

        def balance_sort(page: int, per_page: int = 10):

            embed = discord.Embed(title=f'{ui_localization.get("profile").get("Profile_Pocket").get(LANG)} {user_name}', colour=discord.Colour(int('5BC1FF', 16)))
            embed.add_field(name=f'{ui_localization.get("profile").get("Profile_Currency").get(LANG)}', value=coins)

            start = (page - 1) * per_page
            end = start + per_page
            dictlist = []

            for key, value in inventory_data.items():
                temp = (key, value)
                dictlist.append(temp)

            balance_page = dictlist[start:end]
            pattern = r'[0-9]'

            fullest_items = full_items | rpg_quest_items

            for i, (item_name, data) in enumerate(balance_page, start=start + 1):
                new_string = re.sub(pattern, '', item_name)
                if new_string.replace('📌', '') in fullest_items:
                    item_name, multiplier_price, description, usage, shop_price = (fullest_items
                    .get(
                        new_string.replace('📌', '').strip()))

                    if new_string in all_fish.keys():
                        word = "см" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("cm").get(LANG)}"
                    else:
                        word = "монет" if LANG == "LANG_RU" else f"{ui_localization.get("values").get("coins").get(LANG)}"
                    embed.add_field(name=str(new_string), value=f'{data.get("price") if not isinstance(data, int) else data} {word}')

            if not (inventory_data == {}):
                embed.set_footer(
                    text=f"{ui_localization.get("profile").get("Profile_Page").get(LANG)} {page}/{(len(inventory_data.items()) + per_page - 1) // per_page}"
                )
            else:
                embed.set_footer(
                    text=f"{ui_localization.get("profile").get("Profile_Page").get(LANG)} {page}/1"
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
                @discord.ui.button(label=f"{ui_localization.get("profile").get("Profile_Button_Previous").get(LANG)}", style=discord.ButtonStyle.primary)
                async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                    nonlocal current_page
                    if current_page > 1:
                        current_page -= 1
                        await interaction.response.edit_message(embed=balance_sort(current_page, per_page), view=self)

                @discord.ui.button(label=f"{ui_localization.get("profile").get("Profile_Button_Next").get(LANG)}", style=discord.ButtonStyle.primary)
                async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                    nonlocal current_page
                    max_pages = (len(inventory_data.items()) + per_page - 1) // per_page
                    if current_page < max_pages:
                        current_page += 1
                        await interaction.response.edit_message(embed=balance_sort(current_page, per_page), view=self)

        await ctx.send(embed=embed, view=BalanceView())

    @app_commands.command(name="location", description="Показывает на какой локации ты находишься и с чем можешь взаимодействовать.")
    async def location(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        lore_data = rpg_stuff_ref.child(str(user_id)).get()
        LANG = f"LANG_{servers_ref.child(str(interaction.guild_id)).child("LANGUAGE").get()}"

        # if user_id in in_dialogues:
        #     await interaction.response.send_message(f"ты уже смешарик, подожди 1,5 минуты перед началом нового диалога", ephemeral=True)
        #     return
        # else:
        #     in_dialogues.append(user_id)

        if lore_data is None:
            rpg_stuff_ref.child(str(user_id)).set({
            "current_quest": "None",
            "current_lore": "None",
            "location": "1"
         })

        try:
            current_quest = int(lore_data.get("current_quest")) if lore_data else None
        except:
            current_quest = lore_data.get("current_quest") if lore_data else None

        LOCATION = int(lore_data.get("location")) if lore_data else 1

        class DialogueView(discord.ui.View):
            def __init__(self, npc_emoji, location, userid):
                super().__init__(timeout=90)

                self.userid = userid
                self.npc_emoji = npc_emoji
                self.quest = current_quest
                self.location = location
                self.user_inventory = inventory_ref.child(str(user_id)).get()


                requirements_str = (rpg_lore_quests.get(npc_emoji).get(location).get(self.quest).get("requirements") if self.quest is not None else 1)

                quest_context = {
                    1: {
                        're': re,
                        'str': str,
                        'sum': sum,
                        'inventory_ref': inventory_ref,
                        'fish_book': fish_book,
                        'user_id': self.userid
                    }
                }

                context = quest_context.get(self.quest, {}) if self.quest is not None else {}
                self.requirements = eval(requirements_str, context) if self.quest is not None else 1

                self.dialogue = rpg_lore_quests.get(npc_emoji).get(location).get(self.quest).get("lines").get(LANG) if self.requirements else rpg_lore_quests.get(npc_emoji).get(location).get(self.quest).get("meet_no_requirements").get(LANG)
                self.current_index = -1
                self.update_buttons()

            def update_buttons(self):
                self.clear_items()

                back_btn = discord.ui.Button(
                    emoji="👈",
                    style=discord.ButtonStyle.secondary,
                    disabled=self.current_index == -1
                )
                back_btn.callback = self.go_back

                next_btn = discord.ui.Button(
                    emoji='👉',
                    style=discord.ButtonStyle.secondary,
                    disabled=self.current_index >= len(self.dialogue) - 1
                )
                next_btn.callback = self.go_next

                end_btn = discord.ui.Button(
                    emoji='🖐️',
                    style=discord.ButtonStyle.primary
                )

                end_btn.callback = self.end_dialogue


                self.add_item(back_btn)
                self.add_item(next_btn)

                if self.current_index >= len(self.dialogue) - 1 and self.requirements:
                    self.add_item(end_btn)


            def get_current_message(self):
                if self.current_index < len(self.dialogue):
                    return self.dialogue[self.current_index]

            async def go_back(self, interaction: discord.Interaction):
                if interaction.user.id != self.userid:
                    return await interaction.response.send_message("🗣️❌", ephemeral=True)

                if self.current_index > 0:
                    self.current_index -= 1
                    self.update_buttons()

                dialogue_embed = discord.Embed(
                    title="🗣️",
                    description=f"{speech_bubble(self.get_current_message(), self.npc_emoji)}"
                )

                await interaction.response.edit_message(embed=dialogue_embed, view=self)

            async def go_next(self, interaction: discord.Interaction):
                if interaction.user.id != self.userid:
                    return await interaction.response.send_message("🗣️❌", ephemeral=True)

                if self.current_index < len(self.dialogue) - 1:
                    self.current_index += 1
                    self.update_buttons()

                    dialogue_embed = discord.Embed(
                        title="🗣️",
                        description=f"{speech_bubble(self.get_current_message(), self.npc_emoji)}"
                    )

                    await interaction.response.edit_message(embed=dialogue_embed, view=self)
                else:
                    await interaction.response.edit_message(view=None)


            async def quest_giver(self):
                rpg_stuff_ref.child(str(user_id)).update({
                    "current_quest": rpg_lore_quests.get(self.npc_emoji).get(self.location).get(self.quest).get("new_quest_id")
                })

            async def end_dialogue(self, interaction: discord.Interaction):
                if interaction.user.id != self.userid:
                    return await interaction.response.send_message("🗣️❌", ephemeral=True)

                dialogue_embed = discord.Embed(title=f"🗣️", description=speech_bubble(rpg_lore_quests.get(self.npc_emoji).get(self.location).get(self.quest).get("end_line").get(LANG), self.npc_emoji),
                                               colour=discord.Colour(int('5BC1FF', 16)))
                await interaction.response.edit_message(
                    embed=dialogue_embed,
                    view=None
                )
                # in_dialogues.pop(user_id)
                await self.quest_giver()

            async def on_timeout(self):
                # in_dialogues.pop(user_id)
                for item in self.children:
                    item.disabled = True
                try:
                    await self.message.edit(view=self)
                except:
                    pass

        class TalkSelect(discord.ui.Select):
            def __init__(self):
                npc_list = locations.get(LOCATION).get("npc")
                options=[
                    discord.SelectOption(label=npc) for npc in npc_list
                ]
                super().__init__(placeholder=locations.get(LOCATION).get("options").get("talk_with").get(LANG), max_values=1, min_values=1, options=options)



            async def callback(self, interaction: discord.Interaction):
                if self.values[0] == "🦸" and LOCATION == 1:
                    dialogue_embed = discord.Embed(title=f"🗣️", description=speech_bubble("...", "🦸"), colour=discord.Colour(int('5BC1FF', 16)))
                    view = DialogueView(
                        npc_emoji="🦸",
                        location=LOCATION,
                        userid=interaction.user.id
                    )

                    await interaction.response.edit_message(embed=dialogue_embed, view=view, attachments=[])


        class TalkSelectView(discord.ui.View):
            def __init__(self, *, timeout=180):
                super().__init__(timeout=timeout)
                self.add_item(TalkSelect())



        class RpgSelect(discord.ui.Select):
            def __init__(self):
                options=[
                    discord.SelectOption(label=locations.get(LOCATION).get("options").get("talk").get(LANG))
                ]
                super().__init__(placeholder=locations.get(LOCATION).get("options").get("placeholder").get(LANG), max_values=1, min_values=1, options=options)

            async def callback(self, interaction: discord.Interaction):
                if self.values[0] == locations.get(LOCATION).get("options").get("talk").get(LANG):
                    await interaction.response.edit_message(embed=embed, view=TalkSelectView())



        class RpgSelectView(discord.ui.View):
            def __init__(self, *, timeout=180):
                super().__init__(timeout=timeout)
                self.add_item(RpgSelect())


        embed = discord.Embed(title=f"{locations.get(LOCATION).get("name").get(LANG)}",colour=discord.Colour(int('5BC1FF', 16)))

        src_dir = Path(__file__).parent.parent
        file_path = src_dir / "img" / f"{locations.get(LOCATION).get("place_image")}"

        file = discord.File(file_path, "place.png")
        embed.set_image(url="attachment://place.png")
        embed.add_field(name="", value=f"{locations.get(LOCATION).get("description").get(LANG)}")


        await interaction.response.send_message(embed=embed, view=RpgSelectView(), file=file, ephemeral=True)
async def setup(client):
    await client.add_cog(RPGCog(client))
