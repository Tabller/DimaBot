import asyncio

import discord
from discord.ext import commands
import random

from src.config import active_games, economy_ref

game_emojis = {
    "player": "<:player:1418784679665995907>",
    "biker2": "<:biker2:1418785737209417779>",
    "blank_buck8": "<:blank_buck8:1418785806646251520>",
    "real_buck8": "<:real_buck8:1418785900019847340>",
    "chargeg": "<:chargeg:1418785990884986961>",
    "nocharge": "<:nocharge:1418786156048416949>",
    "hpbracket": "<:hpbracket:1418786228966523011>",
    "bracket": "<:bracket:1418786277372989521>",
    "buckbracket": "<:buckbracket:1418786424551116870>",
    "empty": "<:empty:1418786425054302308>",
    "buckbracket2": "<:buckbracket2:1418786442695413780>",
    "shoot": "<:shoot:1418933098439118919>",
    "inv": "<:inv:1418932733366767626>",
    "mmm": "<:mmm:1418933151182491689>",
    "air": "<:air:1418933217817264149>",
    "items1": "<:items1:1418933358490288239>",
    "items2": "<:items2:1418933513511768186>",
    "items3": "<:items3:1418933560772923412>",
    "items4": "<:items4:1418933602984529991>"
}

class BikeGame:
    def __init__(self, nickname):
        self.quantity_of_bullets = random.randint(2, 8)
        self.player = Entity(nickname)
        self.dealer = Biker(self.quantity_of_bullets)
        self.turn = 1
        self.animation = None
        self.shotgun = Shotgun()
        self.g_embed = discord.Embed(colour=discord.Colour(int('768053', 16)))
        self.insert_shells = lambda: self.shotgun.insert([Ammo("live") for _ in range(self.quantity_of_bullets // 2)] + [Ammo("blank") for _ in range(self.quantity_of_bullets - (self.quantity_of_bullets // 2))])
        self.shuffle_clip = lambda: random.shuffle(self.shotgun.clip)
        # self.insert_shells = lambda: self.shotgun.insert([random.choice([Ammo("live"), Ammo('blank')]) for _ in range(self.quantity_of_bullets)])


class Shotgun:
    def __init__(self):
        self.clip = []
    def insert(self, b):
        self.clip += b
class Ammo:
    def __init__(self, b_type: str):
        self.type = b_type

class ItemCell:
    def __init__(self, item_type):
        self.item_type = item_type

class Entity:
    def __init__(self, nickname: str):
        self.nickname = nickname
        self.inventory = [ItemCell(game_emojis.get("air")) for _ in range(8)]
        self.hp = 5
        self.bullets = {
            Ammo("live").type: [1, "ЖИВАЯ"],
            Ammo("blank").type: [0, "ХОЛОСТАЯ (Не замужем)"]
        }

    def shoot(self, game, gun, who):
        animations = {
            "player": {
                "dealer": {
                0: "https://cdn.discordapp.com/attachments/1181203559191154708/1418280690411245638/PtoD-blank.gif?ex=68ce3512&is=68cce392&hm=84575e5f6a2226150562bc5feec2f3dcb0d839410e30fab80232b148c29e9b80&",
                1: "https://cdn.discordapp.com/attachments/1181203559191154708/1418292686867267746/PtoD-buck.gif?ex=68ce403f&is=68cceebf&hm=1bd2710d70a440d1797401764ae213c48f0127a05d78c8565252d4a45a57edb4&"
                }
            },
            "dealer": {
                "player": {
                0: "https://cdn.discordapp.com/attachments/1181203559191154708/1418297130849665154/DtoP-blank.gif?ex=68ce4462&is=68ccf2e2&hm=034c9b094fc5685ef3ec2acbfaf506e07bd2ea7f2db0b9868d1ac11c54735692&",
                1: "https://cdn.discordapp.com/attachments/1181203559191154708/1418297111048491171/DtoP-buck.gif?ex=68ce445d&is=68ccf2dd&hm=5a5e05837310a0c4b159b0487b73c31f1cf51c329a40175bb6fa843eb991c43f&"
                }
            }
        }

        damage, sentence = self.bullets.get(gun.clip[0].type)

        animation_user = 'player' if game.turn == 1 else 'dealer'
        animation_opponent = 'player' if who == 1 else 'dealer'

        user = lambda choice: game.player if choice == 1 else game.dealer
        user(who).hp -= damage
        gun.clip.pop(0)

        try:
            animation = animations.get(animation_user).get(animation_opponent).get(damage)
        except:
            animation = None


        if damage:
            game.turn = not game.turn
        else:
            if user(who).nickname != self.nickname:
                game.turn = not game.turn
            else:
                pass

        if animation is not None:
            # game.g_embed = discord.Embed(colour=discord.Colour(int('768053', 16)),
            #                        title=f'Байкшотинг {game.player.nickname}')
            # game.g_embed.set_image(url=animation)
            game.animation = animation

        game.g_embed.remove_field(0)
        game.g_embed.remove_field(1)

        return (f"\n{self.nickname} короче стреляет в... {user(who).nickname}, но пулька оказалась... {sentence}"
                f"\n## {game_emojis.get("biker2")} {game.dealer.nickname}"
                f"\n### {game_emojis.get("hpbracket")}{game_emojis.get("chargeg") * game.dealer.hp}{game_emojis.get("nocharge") * (5 - game.dealer.hp)}{game_emojis.get("bracket")}\n"
                f"{game_emojis.get("mmm")}{game_emojis.get("items1")}{''.join([itemcell.item_type for itemcell in game.dealer.inventory[0:4]])}{game_emojis.get("items2")}\n"
                f"{game_emojis.get("mmm")}{game_emojis.get("items3")}{''.join([itemcell.item_type for itemcell in game.dealer.inventory[4:8]])}{game_emojis.get("items4")}\n"
                f"\n## {game_emojis.get("player")} {game.player.nickname}"
                f"\n### {game_emojis.get("hpbracket")}{game_emojis.get("chargeg") * game.player.hp}{game_emojis.get("nocharge") * (5 - game.player.hp)}{game_emojis.get("bracket")}\n"
                f"{game_emojis.get("mmm")}{game_emojis.get("items1")}{''.join([itemcell.item_type for itemcell in game.player.inventory[0:4]])}{game_emojis.get("items2")}\n"
                f"{game_emojis.get("mmm")}{game_emojis.get("items3")}{''.join([itemcell.item_type for itemcell in game.player.inventory[4:8]])}{game_emojis.get("items4")}\n"
                )

class Biker(Entity):
    def __init__(self, quantity):
        super().__init__("Biker")
        self.memory = ["???" for _ in range(quantity)] # здесь задумка про ai норм

    def think(self, game, gun):
        if [bullet.type == "live" for bullet in gun.clip].count(True) >= [bullet.type == "blank" for bullet in gun.clip].count(True):
            return self.shoot(game, gun, 1)
        else:
            return self.shoot(game, gun, 0)




class MiniGamesCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def bikeshot(self, ctx):
        user_id = ctx.author.id
        if user_id in active_games:
            await ctx.send(f"ты уже смешарик, доиграй сначала")
            return

        active_games[user_id] = True

        class GameView(discord.ui.View):
            def __init__(self, author, timeout=60):
                super().__init__(timeout=timeout)
                self.author = author
                self.future = asyncio.Future()
                self.setup_initial_buttons()

            async def zero_callback(self, interaction: discord.Interaction):
                if interaction.user.id != self.author.id:
                    await interaction.response.send_message("не по понятиям в чужие игры лезть", ephemeral=True)
                    return
                await interaction.response.defer()
                self.future.set_result(0)
                self.stop()

            async def one_callback(self, interaction: discord.Interaction):
                if interaction.user.id != self.author.id:
                    await interaction.response.send_message("не по понятиям в чужие игры лезть", ephemeral=True)
                    return
                await interaction.response.defer()
                self.future.set_result(1)
                self.stop()


            async def inventory_callback(self, interaction: discord.Interaction):
                if interaction.user.id != self.author.id:
                    await interaction.response.send_message("не по понятиям в чужие игры лезть", ephemeral=True)
                    return
                await interaction.response.send_message("к сожалению, инвентарь пока что не реализован", ephemeral=True)

            async def shoot_callback(self, interaction: discord.Interaction):
                if interaction.user.id != self.author.id:
                    await interaction.response.send_message("не по понятиям в чужие игры лезть", ephemeral=True)
                    return
                self.setup_choice_buttons()

                GameEntity.g_embed = discord.Embed(colour=discord.Colour(int('768053', 16)),
                                   title=f'Байкшотинг {ctx.author.display_name}', description="Выберите байкера или себя")
                await  message.edit(embed=GameEntity.g_embed, view=view)
                await interaction.response.edit_message(view=self)

            def setup_initial_buttons(self):
                self.clear_items()

                inventory_btn = discord.ui.Button(
                    label='',
                    style=discord.ButtonStyle.grey,
                    emoji=game_emojis.get('inv'),
                    custom_id='inventory'
                )
                inventory_btn.callback = self.inventory_callback
                self.add_item(inventory_btn)

                shoot_btn = discord.ui.Button(
                    label='',
                    style=discord.ButtonStyle.grey,
                    emoji=game_emojis.get('shoot'),
                    custom_id='shoot'
                )
                shoot_btn.callback = self.shoot_callback
                self.add_item(shoot_btn)

            def setup_choice_buttons(self):
                self.clear_items()

                zero_btn = discord.ui.Button(
                    label='',
                    style=discord.ButtonStyle.success,
                    emoji=game_emojis.get('biker2'),
                    custom_id='zero'
                )
                zero_btn.callback = self.zero_callback
                self.add_item(zero_btn)

                one_btn = discord.ui.Button(
                    label='',
                    style=discord.ButtonStyle.success,
                    emoji=game_emojis.get('player'),
                    custom_id='one'
                )
                one_btn.callback = self.one_callback
                self.add_item(one_btn)

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                if interaction.user.id == self.author.id:
                    return True

            async def on_timeout(self) -> None:
                GameEntity.g_embed = discord.Embed(colour=discord.Colour(int('768053', 16)),
                                   title=f'Байкшотинг {ctx.author.display_name}', description=f"ёмаё ну ты чёто долго думаеш, байкер ушёл")
                await message.edit(embed=GameEntity.g_embed, view=None)
                active_games.pop(user_id, None)
                return


        GameEntity = BikeGame(ctx.author.display_name)
        GameEntity.insert_shells()
        GameEntity.shuffle_clip()
        GameEntity.g_embed = discord.Embed(colour=discord.Colour(int('768053', 16)),
                                   title=f'Байкшотинг {ctx.author.display_name}')

        message = await ctx.send(embed=GameEntity.g_embed)

        async def fill_animation(live_bullet, blank_bullet):
            blank_b = game_emojis.get("blank_buck8")
            real_b = game_emojis.get("real_buck8")
            empty = game_emojis.get("empty")
            a = [real_b for _ in range(live_bullet)] + [blank_b for _ in range(blank_bullet)]
            b = [empty] * len(a)

            i = 0

            for _ in b:
                index = random.randrange(len(a))
                element = a.pop(index)
                b[i] = element
                g = "".join(b)
                GameEntity.g_embed.description = f"короче сегодня вот такой расклад \n## {game_emojis.get("buckbracket")} {g} {game_emojis.get("buckbracket2")}"
                await message.edit(embed=GameEntity.g_embed)
                i += 1
                await asyncio.sleep(1.5)

            GameEntity.g_embed.description += f"\n-# {live_bullet} живых и {blank_bullet} пустых пулек"
            await message.edit(embed=GameEntity.g_embed)

        await fill_animation([bullet.type == "live" for bullet in GameEntity.shotgun.clip].count(True), [bullet.type == "blank" for bullet in GameEntity.shotgun.clip].count(True))
        await asyncio.sleep(7)
        GameEntity.g_embed.description = "..."
        await  message.edit(embed=GameEntity.g_embed)
        await asyncio.sleep(2)

        while True:
            if GameEntity.player.hp == 0 or GameEntity.dealer.hp == 0:
                detect = lambda: GameEntity.player.nickname if GameEntity.player.hp == 0 else GameEntity.dealer.nickname
                GameEntity.g_embed.description = f"увы, сегодня проиграл {detect()}"
                await message.edit(embed=GameEntity.g_embed)
                active_games.pop(user_id, None)
                break

            if len(GameEntity.shotgun.clip) == 0:
                GameEntity.quantity_of_bullets = random.randint(4, 8)
                GameEntity.insert_shells()
                GameEntity.shuffle_clip()

                await fill_animation([bullet.type == "live" for bullet in GameEntity.shotgun.clip].count(True),
                                     [bullet.type == "blank" for bullet in GameEntity.shotgun.clip].count(True))

                await asyncio.sleep(7)
                GameEntity.g_embed.description = "..."
                await  message.edit(embed=GameEntity.g_embed)
                await asyncio.sleep(2)

            now = lambda which_move: "ВАШ ход"if GameEntity.turn else "БАЙКЕРСКИЙ ход"
            GameEntity.g_embed.description = f"{now(GameEntity.turn)}"
            await  message.edit(embed=GameEntity.g_embed)
            await asyncio.sleep(3)
            GameEntity.g_embed.description = "..."
            await  message.edit(embed=GameEntity.g_embed)
            await asyncio.sleep(2)



            if GameEntity.turn:
                GameEntity.g_embed.remove_field(0)
                GameEntity.g_embed.remove_field(1)
                view = GameView(ctx.author, timeout=60)
                GameEntity.g_embed.add_field(name=f"{game_emojis.get("inv")}**ИНВЕНТАРЬ**", value="Пока что недоступен (WIP)", inline=True)
                GameEntity.g_embed.add_field(name=f"{game_emojis.get("shoot")}**ДРОБОВИК**", value="Взять дробовик\nи выстрелить", inline=True)
                GameEntity.g_embed.description = (
                f"\n## {game_emojis.get("biker2")} {GameEntity.dealer.nickname}"
                f"\n### {game_emojis.get("hpbracket")}{game_emojis.get("chargeg") * GameEntity.dealer.hp}{game_emojis.get("nocharge") * (5 - GameEntity.dealer.hp)}{game_emojis.get("bracket")}\n"
                f"{game_emojis.get("mmm")}{game_emojis.get("items1")}{''.join([itemcell.item_type for itemcell in GameEntity.dealer.inventory[0:4]])}{game_emojis.get("items2")}\n"
                f"{game_emojis.get("mmm")}{game_emojis.get("items3")}{''.join([itemcell.item_type for itemcell in GameEntity.dealer.inventory[4:8]])}{game_emojis.get("items4")}\n"
                f"\n## {game_emojis.get("player")} {GameEntity.player.nickname}"
                f"\n### {game_emojis.get("hpbracket")}{game_emojis.get("chargeg") * GameEntity.player.hp}{game_emojis.get("nocharge") * (5 - GameEntity.player.hp)}{game_emojis.get("bracket")}\n"
                f"{game_emojis.get("mmm")}{game_emojis.get("items1")}{''.join([itemcell.item_type for itemcell in GameEntity.player.inventory[0:4]])}{game_emojis.get("items2")}\n"
                f"{game_emojis.get("mmm")}{game_emojis.get("items3")}{''.join([itemcell.item_type for itemcell in GameEntity.player.inventory[4:8]])}{game_emojis.get("items4")}\n"
                )
                await  message.edit(embed=GameEntity.g_embed, view=view)

                try:
                    choice = await view.future
                except asyncio.TimeoutError:
                    GameEntity.g_embed.description = f"ёмаё ну ты чёто долго думаеш, байкер ушёл"
                    await message.edit(embed=GameEntity.g_embed)
                    active_games.pop(user_id, None)
                    return

                GameEntity.g_embed.remove_field(0)
                GameEntity.g_embed.remove_field(1)



                description = GameEntity.player.shoot(GameEntity, GameEntity.shotgun, choice)

                if GameEntity.animation is not None:
                    GameEntity.g_embed = discord.Embed(colour=discord.Colour(int('768053', 16)),
                                       title=f'Байкшотинг {ctx.author.display_name}')
                    GameEntity.g_embed.set_image(url=GameEntity.animation)
                    await message.edit(embed=GameEntity.g_embed, view=None)
                    await asyncio.sleep(2.33)
                    GameEntity.g_embed.set_image(url=None)
                    GameEntity.animation = None

                GameEntity.g_embed.description = f"{description}"
                await message.edit(embed=GameEntity.g_embed, view=None)
                await asyncio.sleep(5)
                GameEntity.g_embed.set_image(url=None)
                GameEntity.g_embed.description = "..."
                await  message.edit(embed=GameEntity.g_embed)
                await asyncio.sleep(2)

            else:
                description = GameEntity.dealer.think(GameEntity, GameEntity.shotgun)
                if GameEntity.animation is not None:
                    GameEntity.g_embed = discord.Embed(colour=discord.Colour(int('768053', 16)),
                                       title=f'Байкшотинг {ctx.author.display_name}')
                    GameEntity.g_embed.set_image(url=GameEntity.animation)
                    await message.edit(embed=GameEntity.g_embed, view=None)
                    await asyncio.sleep(2.33)
                    GameEntity.g_embed.set_image(url=None)
                    GameEntity.animation = None
                GameEntity.g_embed.description = f"{description}"
                await message.edit(embed=GameEntity.g_embed)
                await asyncio.sleep(5)
                GameEntity.g_embed.set_image(url=None)
                GameEntity.g_embed.description = "..."
                await  message.edit(embed=GameEntity.g_embed)
                await asyncio.sleep(2)



async def setup(client):
    await client.add_cog(MiniGamesCog(client))