import asyncio

import discord
from discord.ext import commands
import random

from src.config import active_games, economy_ref

game_emojis = {
    "player": "<:player:1418268662506197012>",
    "biker2": "<:biker2:1418268825538793492>",
    "blank_buck8": "<:blank_buck8:1418268907533369394>",
    "real_buck8": "<:real_buck8:1418268960368889876>",
    "chargeg": "<:chargeg:1418269033836318922>",
    "nocharge": "<:nocharge:1418269272307667014>",
    "hpbracket": "<:hpbracket:1418269272798531604>",
    "bracket": "<:bracket:1418269273717215434>",
    "buckbracket": "<:buckbracket:1418274527913185290>",
    "empty": "<:empty:1418274528810893372>",
    "buckbracket2": "<:buckbracket2:1418274529523798117>"
}

class BikeGame:
    def __init__(self, nickname):
        self.quantity_of_bullets = random.randint(2, 8)
        self.player = Entity(nickname)
        self.dealer = Biker(self.quantity_of_bullets)
        self.turn = 1
        self.shotgun = Shotgun()
        self.g_embed = discord.Embed(colour=discord.Colour(int('F54927', 16)))
        self.insert_shells = lambda: self.shotgun.insert([Ammo("live") for _ in range(self.quantity_of_bullets // 2)] + [Ammo("blank") for _ in range(self.quantity_of_bullets - (self.quantity_of_bullets // 2))])
        # self.insert_shells = lambda: self.shotgun.insert([random.choice([Ammo("live"), Ammo('blank')]) for _ in range(self.quantity_of_bullets)])


class Shotgun:
    def __init__(self):
        self.clip = []
    def insert(self, b):
        self.clip += b
class Ammo:
    def __init__(self, b_type: str):
        self.type = b_type

class Entity:
    def __init__(self, nickname: str):
        self.nickname = nickname
        self.hp = 3
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
            game.g_embed.set_image(url=animation)
        return f"\n{self.nickname} короче стреляет в... {user(who).nickname}, но пулька оказалась... {sentence}\n## {game_emojis.get("player")} {game.player.nickname}\n# {game_emojis.get("chargeg") * game.player.hp}\n\n## {game_emojis.get("biker2")} {game.dealer.nickname}\n# {game_emojis.get("chargeg") * game.dealer.hp}"

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
            def __init__(self, author, timeout=15):
                super().__init__(timeout=timeout)
                self.author = author
                self.future = asyncio.Future()

            @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji='0️⃣')
            async def zero(self, interaction: discord.Interaction, button: discord.Button):
                if interaction.user.id != self.author.id:
                    await interaction.response.send_message("не по понятиям в чужие игры лезть", ephemeral=True)
                    return
                await interaction.response.defer()
                self.future.set_result(0)
                self.stop()

            @discord.ui.button(label='', style=discord.ButtonStyle.success, emoji='1️⃣')
            async def one(self, interaction: discord.Interaction, button: discord.Button):
                if interaction.user.id != self.author.id:
                    await interaction.response.send_message("не по понятиям в чужие игры лезть", ephemeral=True)
                    return
                await interaction.response.defer()
                self.future.set_result(1)
                self.stop()

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                return interaction.user.id == self.author.id

        GameEntity = BikeGame(ctx.author.display_name)
        GameEntity.insert_shells()

        GameEntity.g_embed = discord.Embed(colour=discord.Colour(int('F54927', 16)),
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
                GameEntity.g_embed.description = f"короче сегодня вот \n## {game_emojis.get("buckbracket")} {g} {game_emojis.get("buckbracket2")}"
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
                if GameEntity.player.hp == 0:
                    user_data = economy_ref.child(str(ctx.author.id)).get()

                    if "player" in user_data:
                        pass
                    else:
                        economy_ref.child(str(ctx.author.id)).child("player").set("😃👔🖐👖")
                        user_data = economy_ref.child(str(ctx.author.id)).get()

                    if "health" in user_data:
                        pass
                    else:
                        economy_ref.child(str(ctx.author.id)).child("health").set("5")
                        user_data = (economy_ref.child(str(ctx.author.id)).get())

                    economy_ref.child(str(ctx.author.id)).child("health").set(int(user_data["health"]) - 1)

                active_games.pop(user_id, None)
                break

            if len(GameEntity.shotgun.clip) == 0:
                GameEntity.quantity_of_bullets = random.randint(4, 8)
                GameEntity.insert_shells()

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
                view = GameView(ctx.author, timeout=15)
                GameEntity.g_embed.description = f"{now(GameEntity.turn)}\nВыберите 0 - байкера; 1 - себя"
                await  message.edit(embed=GameEntity.g_embed, view=view)

                try:
                    choice = await view.future
                except asyncio.TimeoutError:
                    GameEntity.g_embed.description = f"ёмаё ну ты чёто долго думаеш, байкер ушёл"
                    await message.edit(embed=GameEntity.g_embed)
                    active_games.pop(user_id, None)
                    return

                GameEntity.g_embed.description = f"{GameEntity.player.shoot(GameEntity, GameEntity.shotgun, choice)}"
                await message.edit(embed=GameEntity.g_embed, view=None)
                await asyncio.sleep(5)
                GameEntity.g_embed.set_image(url=None)
                GameEntity.g_embed.description = "..."
                await  message.edit(embed=GameEntity.g_embed)
                await asyncio.sleep(2)

            else:
                GameEntity.g_embed.description = f"{GameEntity.dealer.think(GameEntity, GameEntity.shotgun)}"
                await message.edit(embed=GameEntity.g_embed)
                await asyncio.sleep(5)
                GameEntity.g_embed.set_image(url=None)
                GameEntity.g_embed.description = "..."
                await  message.edit(embed=GameEntity.g_embed)
                await asyncio.sleep(2)



async def setup(client):
    await client.add_cog(MiniGamesCog(client))