import random

import discord
from discord import ui
from discord.ext import commands

from src.config import FEEDBACK_CHANNEL_ID, servers_ref, ui_localization


class Menu(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

class OtherCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.hybrid_command()
    async def feedback(self, ctx, *, text):
        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"
        message_time = ctx.message.created_at
        author = ctx.author
        jump_url = ctx.message.jump_url
        channel = self.client.get_channel(ctx.channel.id) if hasattr(ctx.channel, 'name') else 'DM'
        embed = discord.Embed(description=text, title=f"{ui_localization.get("feedback").get("feedback_title1").get(LANG)} ft. {ui_localization.get("feedback").get("feedback_title2").get(LANG)}").set_footer(text=ctx.author.display_name,
                                                                                       icon_url=ctx.author.avatar.url)

        class AnswerForm(ui.Modal, title=f'{ui_localization.get("feedback").get("feedback_answer").get(LANG)}'):
            Field = ui.TextInput(label=f"{ui_localization.get("feedback").get("feedback_text").get(LANG)}")

            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.defer(ephemeral=True)
                response = self.Field.value
                embed4 = discord.Embed(description=f'{ui_localization.get("feedback").get("feedback_reply").get(LANG)}: {response}')
                embed4.add_field(name=" ", value=f"[{ui_localization.get("feedback").get("feedback_message_url").get(LANG)}]({jump_url})", inline=False)
                embed4.set_footer(text=f"{interaction.user.display_name} {ui_localization.get("feedback").get("feedback_reply_msg1").get(LANG)}: {message_time.strftime("%d.%m.%Y")} {ui_localization.get("feedback").get("feedback_reply_msg2").get(LANG)} {author}", icon_url=interaction.user.avatar.url)
                await channel.send(embed=embed4)


        class AnswerButton(discord.ui.View):
            @discord.ui.button(label=f'{ui_localization.get("feedback").get("feedback_reply_button").get(LANG)}', style=discord.ButtonStyle.success)
            async def respond3(self, interaction: discord.Interaction, item):
                await interaction.response.send_modal(AnswerForm())
           #    await interaction.edit_original_response(view=None)
        send_feedback = await self.client.get_channel(int(FEEDBACK_CHANNEL_ID)).send(embed=embed,
                                                                                view=AnswerButton(timeout=None))

        await ctx.send(f'{ui_localization.get("feedback").get("feedback_sent").get(LANG)}')

    @commands.hybrid_command()
    async def test(self, ctx, *, arg):
        await ctx.send(arg)

    @commands.hybrid_command()
    async def meme(self, ctx):
        links = ['https://tenor.com/view/%D1%86%D0%B2%D0%B5%D1%82%D1%8B-%D1%87%D0%B0%D0%B9-gif-402293663251947105',
                 'https://medal.tv/ru/games/minecraft/clips/jJYaWupK5FPvcuyIA?invite=cr-MSxtdEcsMTQxNjg3NzEzLA',
                 'https://medal.tv/ru/games/minecraft/clips/jJY835WlKTgizxlQ9?invite=cr-MSxxblIsMTQxNjg3NzEzLA',
                 'https://medal.tv/ru/games/minecraft/clips/jJY70nnSokD8toCJ9?invite=cr-MSxIcGwsMTQxNjg3NzEzLA',
                 'https://tenor.com/view/cat-vro-mei-mei-mei-tole-tole-gif-12564264859640410840',
                 'https://tenor.com/view/cat-brain-cat-brain-ice-cream-gif-25160275',
                 'https://medal.tv/ru/games/roblox/clips/jFznrb3IsHB56g54M?invite=cr-MSw1T0QsMTQxNjg3NzEzLA',
                 'https://www.twitch.tv/mrtomit/clip/GorgeousPoisedAlfalfaTakeNRG-eLgJor8iJtWB3QZF',
                 'https://www.twitch.tv/mrtomit/clip/FitEasyKeyboardCoolStoryBob-2Gsd_aYYD9jpGtUg',
                 'https://www.twitch.tv/mrtomit/clip/IntelligentRelentlessCurlewBrainSlug-s0wWdky0tqSnkQrj',
                 'https://medal.tv/ru/games/minecraft/clips/jwnWpNg7UDR-3-iHv?invite=cr-MSxTU08sMTQxNjg3NzEzLA',
                 'https://tenor.com/view/mee6-gif-24405001',
                 'https://media.discordapp.net/attachments/1051934380924338186/1070396001069830164/tomatloh.gif?ex=67cc7ef5&is=67cb2d75&hm=02f587046e1bc2b06d110ad1fe94fceb59a4838feea657a69ac233346a158424&',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1215755642887733279/caption_2.gif?ex=67cca62c&is=67cb54ac&hm=e30478da92d22cc414b63636b6c64b84296192b2262c5aa6406487763972a9ad&',
                 'https://tenor.com/view/mod-purge-discord-mods-i-hate-this-server-moderation-team-mods-gif-25676559',
                 'https://medal.tv/ru/games/roblox/clips/jshIdvtCYSb63cNCX?invite=cr-MSx6V3MsMTQxNjg3NzEzLA',
                 'https://medal.tv/ru/games/roblox/clips/jsfwZDchKGDMHnHpD?invite=cr-MSxOWm4sMTQxNjg3NzEzLA',
                 'https://media.discordapp.net/attachments/514133658529955860/1090354788757151985/caption.gif?ex=67cc9887&is=67cb4707&hm=53bbfc5df69be22d5ea11a447da353860b731d5afec923aa9dcc67fd984ac537&',
                 'https://cdn.discordapp.com/attachments/514133658529955860/1325466408846495764/caption.gif?ex=67ccf889&is=67cba709&hm=ff1f197744a3238fc00a0def19bdf6ccf6610bfa206d6740ca7bdf09da1267fd&',
                 'https://cdn.discordapp.com/attachments/514133658529955860/1260302509122129992/caption.gif?ex=67cc8d2d&is=67cb3bad&hm=b7c54bbd078100cfcf18d9aeaa5fc1bd11624341d3c9c7057ff3b8253dfc8359&',
                 'https://media.discordapp.net/attachments/553533944063328258/998448833384165436/gif_1.gif?ex=67cc72b0&is=67cb2130&hm=99e69ccb13faf0ae5fad122b1a3699110abdc1b39c9efade2119098ce1a0bda0&',
                 'https://medal.tv/ru/games/minecraft/clips/jn2XHhdUnLvMgvVRu?invite=cr-MSxpT04sMTQxNjg3NzEzLA',
                 'https://tenor.com/view/whatsapp-gif-21302024',
                 'https://medal.tv/ru/games/roblox/clips/ji1m01PfySaoovvHf?invite=cr-MSw2VjYsMTQxNjg3NzEzLA',
                 'https://medal.tv/ru/games/roblox/clips/jhYcunAnPzurVIq1S?invite=cr-MSw0SW0sMTQxNjg3NzEzLA',
                 'https://medal.tv/ru/games/roblox/clips/ji6rLVePCEVKLLn9F?invite=cr-MSxJa1UsMTQxNjg3NzEzLA',
                 'https://medal.tv/ru/games/roblox/clips/ji2bjrYZVCBQFL-5n?invite=cr-MSxLRFAsMTQxNjg3NzEzLA',
                 'https://tenor.com/view/dr-nefario-fart-gun-gif-20054143',
                 'https://www.twitch.tv/mrtomit/clip/MushyMuddyAnteaterDuDudu-aSMzoKsrMGojjo2J',
                 'https://www.twitch.tv/mrtomit/clip/OilyDullAyeayeRuleFive-HBvwpd_nYK4AYR0C',
                 'https://www.twitch.tv/mrtomit/clip/EnthusiasticAntediluvianBeaverHoneyBadger-I8yyRPltC69tuDbE',
                 'https://www.twitch.tv/mrtomit/clip/MoralHonorableInternRalpherZ-_-PUox4KXRgWwGJU',
                 'https://www.twitch.tv/mrtomit/clip/BoringZealousBeefWoofer-VOXHq9cxRk9YUSKS',
                 'https://tenor.com/view/average-conversation-in-this-server-discord-server-donowall-ignored-gif-2054677438560113125',
                 'https://tenor.com/view/alexs-caves-orb-primordial-caves-puss-in-boots-jack-horner-gif-27498505',
                 'https://medal.tv/ru/games/minecraft/clips/j41c7aexClFC6nwd8?invite=cr-MSxvZHUsMTQxNjg3NzEzLA',
                 'https://tenor.com/view/adequate-rules-say-it-and-u%27ll-be-muted-gif-701907492395044116',
                 'https://medal.tv/ru/games/buckshot-roulette/clips/j2poCpkE5nGqNIQ_k?invite=cr-MSxreTQsMTQxNjg3NzEzLA',
                 'https://www.youtube.com/watch?v=WAkQKVdP9Eo',
                 'https://tenor.com/view/green-alien-cat-green-alien-green-cat-alien-gif-721538137659195618',
                 'https://tenor.com/view/not-a-sigma-sorry-you-are-not-a-sigma-sorry-you%27re-not-a-sigma-you-aren%27t-a-sigma-you-are-not-sigma-gif-337838532227751572',
                 'https://tenor.com/view/mystical-wise-tree-a-little-goofy-omg-rofl-lmfao-gif-3707288582733751132',
                 'https://tenor.com/view/da-gif-10183464272850732800',
                 'https://cdn.discordapp.com/emojis/1098375901248487424.gif?size=48&quality=lossless&name=tomatjret',
                 'https://tenor.com/view/cat-funny-cat-funny-smile-happy-gif-7621419476068285580',
                 'https://www.twitch.tv/mrtomit/clip/ClumsyFriendlyPeafowlCharlietheUnicorn-p1_hf_ZmOHxCNlwi',
                 'https://www.twitch.tv/mrtomit/clip/CoweringSingleTruffleTwitchRPG-anHX7unyQd5QpHAw',
                 'https://www.twitch.tv/mrtomit/clip/CuriousLittleCheddarPoooound-kaGI74ieAMs3h2dS',
                 'https://www.twitch.tv/mrtomit/clip/FragileQuaintDotterelAllenHuhu-ZHdHk8J8Usu4E-NN',
                 'https://www.twitch.tv/mrtomit/clip/ClumsyCarelessTermiteWutFace-d5lVNrbrD4pacThE',
                 'https://www.twitch.tv/mrtomit/clip/InnocentTallStapleTooSpicy-7U3mOB4tq37igmMg',
                 'https://www.twitch.tv/mrtomit/clip/ExpensiveInexpensiveMangoAsianGlow-hykemhVcqOOP5rCx',
                 'https://www.twitch.tv/mrtomit/clip/PoliteEagerGiraffeNotATK-6o5MjFttmdgJ2_Kc',
                 'https://www.twitch.tv/mrtomit/clip/PolishedTalentedTaroSmoocherZ-dw3ZOPk-5J32SNP7',
                 'https://www.twitch.tv/mrtomit/clip/TolerantGrotesqueKeyboardTooSpicy-7XPV1rjaHx-RtNVQ',
                 'https://www.twitch.tv/mrtomit/clip/SuperWealthyDurianFutureMan-9BROPxcADpqQS77P',
                 'https://www.twitch.tv/mrtomit/clip/ToughExuberantSproutCharlietheUnicorn-LnEiuLOHGKQswvjv',
                 'https://www.twitch.tv/mrtomit/clip/DifferentWealthyMageTheRinger-68uh9EOGPr6UNYjg',
                 'https://cdn.discordapp.com/attachments/514133658529955860/1273741999169605752/caption.gif?ex=67ccaa2d&is=67cb58ad&hm=8a5596ec48454bae1c7e4c2922a197714f3dacf6a62ce68ac3dcea65132d6596&',
                 'https://tenor.com/view/discord-reaction-gif-23868418',
                 'https://youtu.be/zX2SjdImGc8?si=Xysr-TubGIEkMZXm',
                 'https://clips.twitch.tv/SpinelessBumblingChickenItsBoshyTime-IrCDa27GBWoUEWOa',
                 'https://clips.twitch.tv/MoralTallNigiriFloof-sd9EXhBPQECize_k',
                 'https://cdn.discordapp.com/emojis/1252846764206329906.webp?size=48&quality=lossless&name=smartass',
                 'https://media.discordapp.net/attachments/694981054406066319/1065255144247271524/caption.gif?ex=67cce8e9&is=67cb9769&hm=bef0e13b79e9a07455ed34128134e35cb5cd5c7ea40d13d44f30897833b1ec1a&',
                 'https://tenor.com/view/cat-uncanny-cat-canny-cat-uncanny-canny-gif-2341506220249338090',
                 'https://tenor.com/view/minecraft-create-mod-technology-gif-25752533',
                 'https://tenor.com/view/podolsk-gif-20371232',
                 'https://tenor.com/view/roblox-roblox-meme-roblox-obby-roblox-jumpscare-gif-25132757',
                 'https://tenor.com/view/tushmar-snail-eating-tomato-funny-epic-gif-tushmar-tier3overwatch-coach-tier3overwatch-gif-20907469',
                 'https://tenor.com/view/spinning-tomato-gif-24526359',
                 'https://clips.twitch.tv/GlutenFreeHyperShrimpKlappa-WQLHquJBYOdoFGOj',
                 'https://clips.twitch.tv/CrypticVenomousLlamaBabyRage-l170WlMC13AqjK0F',
                 'https://clips.twitch.tv/GoldenShakingDotterelPartyTime-gZufXanWjjBql55J',
                 'https://clips.twitch.tv/ResourcefulConfidentSwallowPJSugar-qc0CU_MHYJszcgBU',
                 'https://clips.twitch.tv/LittleSilkySnailTheThing-omXZQ7CTuwohHy6Y',
                 'https://tenor.com/view/minecraft-create-aerodynamics-strike-gif-25269807',
                 'https://tenor.com/view/%D0%B0-4-gif-14211769093273171637',
                 'https://cdn.discordapp.com/attachments/305834181949390848/524302853087428618/Screenshot_2018-12-06-15-58-35.png?ex=67cc9695&is=67cb4515&hm=225057b60d58a33494f5d6bd4ce446ba4355fb9dd57316bc0f60b0355f764d09&uc=dp&',
                 'https://tenor.com/view/%E0%B8%95%E0%B8%B2%E0%B8%A2%E0%B9%81%E0%B8%9E%E0%B8%A3%E0%B9%8A%E0%B8%9A-cpr-revive-cat-gif-15837553',
                 'https://tenor.com/view/bogo-moment-bogo-sort-sorting-bogo-sort-moment-bogo-gif-25634188',
                 'https://tenor.com/view/hey-all-scott-here-this-gif-27154582',
                 'https://tenor.com/view/death-corridor-death-corridor-geometry-dash-geometry-gif-15673481441265769442',
                 'https://tenor.com/view/funny-spongebob-gif-17598597586521616942',
                 'https://clips.twitch.tv/GiftedRockySquidVoteNay-ny2FT1oBAobYJhuP',
                 'https://clips.twitch.tv/EnthusiasticEsteemedPidgeonOMGScoots-FI5RTCSWmXaNsR_0',
                 'https://clips.twitch.tv/DeadRespectfulLocustYee-eHifj9sUYoLAR7hu',
                 'https://clips.twitch.tv/CredulousSpotlessPorcupineSaltBae-ddzQ_lrackVQZe5-',
                 'https://clips.twitch.tv/BloodyAlivePhoneWutFace-sdCrtJ0-I8WRM9au',
                 'https://clips.twitch.tv/ManlyIgnorantChamoisKappaClaus-GmtQ4yhMTOVYJw_3',
                 'https://clips.twitch.tv/FurryHotTofuHassanChop-wN_AwzhC9BCFDDMk',
                 'https://clips.twitch.tv/JoyousElegantPeppermintOptimizePrime-Oj00JndiXcgSzd78',
                 'https://clips.twitch.tv/CallousGorgeousMageAliens-ru8Not0PreO5nNVx',
                 'https://tenor.com/view/cat-power-cat-cat-pillow-repost-this-post-this-cat-gif-23865940',
                 'https://tenor.com/view/frog-frog-laughing-gif-25708743',
                 'https://clips.twitch.tv/SincereBoredStarBuddhaBar-Q4W-e2OpENBN7ynD',
                 'https://tenor.com/view/taeuvre-squidward-squidward-shocked-squidward-break-gif-26165410',
                 'https://tenor.com/view/cringe-death-dies-of-cringe-davy-jones-dying-of-cringe-gif-22207406',
                 'https://tenor.com/view/troll-trolled-trollge-troll-success-gif-22597471',
                 'https://media.discordapp.net/attachments/514133658529955860/1072239501851758653/caption.gif?ex=67cc9c5a&is=67cb4ada&hm=d2a7ab87fbd6c8ee3c36b0cbae0a5d5f37ef3dcb2675c79af29bb5e4b43cbe56&',
                 'https://media.discordapp.net/attachments/514133658529955860/1062394076458131466/caption.gif?ex=67cd0c56&is=67cbbad6&hm=0663ec167e0ae83d51e6148b4c1c1e79257d2942d3d21bfcadacb8862d9c2914&',
                 'https://media.discordapp.net/attachments/554288956926066708/1064562754058465300/tomatonline.gif?ex=67cd0713&is=67cbb593&hm=b5b615d74141ecb4930c84a08fcedf674c41f3a57bba1b2ea6e1f9448dd676e3&',
                 'https://media.discordapp.net/attachments/514133658529955860/1060233189500653639/caption.gif?ex=67cd18da&is=67cbc75a&hm=2ac5c0e47a65845a7373793e77fbfda89e1e56ac8810644ea4cbeef06765adf4&',
                 'https://media.discordapp.net/attachments/514133658529955860/1062394612049793044/caption.gif?ex=67cd0cd5&is=67cbbb55&hm=a66061888b8ef2400012cde1c69dcc038172899cd50b3cb3e415df2009a3b514&',
                 'https://tenor.com/view/fat-herobrine-gif-18363356',
                 'https://discord.com/channels/967091313038196796/1253099639000006697/1346842584655462450',
                 'https://discord.com/channels/967091313038196796/1042878735965245512/1339264860487291002',
                 'https://cdn.discordapp.com/attachments/697785285962104872/1300415408918237204/ezgif.com-animated-gif-maker.gif?ex=67cccd7a&is=67cb7bfa&hm=9ec5682253599de080d0b055b70b97f1d27964644012ee23b8e64a19fe1761df&',
                 'https://www.twitch.tv/mrtomit/clip/RealRelentlessCockroachYouDontSay-3UQHDUhVee5eqZW7',
                 'https://www.twitch.tv/mrtomit/clip/FrozenZanyGrassDancingBanana-PMeBkuwbmAXhuAvR',
                 'https://tenor.com/view/amor-gif-10758667656717415642',
                 'https://tenor.com/view/lie-detector-gif-9388384639890532829',
                 'https://www.twitch.tv/mrtomit/clip/BashfulIgnorantFalconPeoplesChamp-eFi5sXgyMJ5gJIC-',
                 'https://www.youtube.com/watch?v=-BP7DhHTU-I',
                 'https://tenor.com/view/fall-falling-fallen-kingdom-fallen-kingdom-gif-6774652182841014167',
                 'https://media.discordapp.net/attachments/1018882963259281459/1100078685018673273/vzriv_pekarni2.gif?ex=67cd08dc&is=67cbb75c&hm=ab172db2fb30ac76bbc18d8288ffabb5a70c96a9c6818e095f1992b200f01021&',
                 'https://tenor.com/view/%D1%82%D1%8B%D0%BE%D1%82%D0%BF%D1%80%D0%B0%D0%B2%D0%BB%D1%8F%D0%B5%D1%88%D1%8C%D1%81%D1%8F%D0%B2%D1%83%D0%B3%D0%BE%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5-gif-26526641',
                 'https://tenor.com/view/fish-react-fish-react-him-thanos-gif-26859685',
                 'https://www.youtube.com/watch?v=DUgcNM-3d5E',
                 'https://media.discordapp.net/attachments/1018882963259281459/1135203069362180166/bonobo_activities.gif?ex=67ccef7e&is=67cb9dfe&hm=e3d3f2fccddce11abcd270862e80009269670c2e0162100516f22a1ddd78960c&',
                 'https://media.discordapp.net/attachments/1051934380924338186/1072860017075691580/tomat_usnul.gif?ex=67cce400&is=67cb9280&hm=6bb218dc13b718c9600ffb89c3282dadf16e75c97df1df8615946192b2dd7645&',
                 'https://youtu.be/H4iWAbaVIMU',
                 'https://discord.com/channels/967091313038196796/1202188402364268544/1227981517133975592',
                 'https://youtu.be/WhVZna5ONlk', 'https://youtu.be/Z5cPWkhM4X0',
                 'https://cdn.discordapp.com/attachments/810191795727237120/1085276447989583952/im_so_excited_about_my_super_weapon_that_will_take_over_watergrad_that_i_wrote_a_song_about_it.mp4?ex=67cc93f4&is=67cb4274&hm=550433c58a90d4ed7423d4a0d5f11acbfc25ad6d5094515a2dd9be959986f339&',
                 'https://media.discordapp.net/attachments/1051934380924338186/1072853000802025512/pov_you_opened_a_chest_in_facility.gif?ex=67ccdd78&is=67cb8bf8&hm=f2fa4bf2fa68b5cca343b86d5dd99925db9f5e662a3e6b95fe1ecf38326f24c6&',
                 'https://youtu.be/AitziTN7gX4',
                 'https://media.discordapp.net/attachments/967091313038196799/1056984343056224256/image.png?width=960&height=330&ex=67cd24a1&is=67cbd321&hm=13c51cd86c4b050977c48c7255d8442a4a51248f48a990b2087fe3b513110a16&',
                 'https://www.youtube.com/watch?v=LF_zoIAZvBs', 'https://www.youtube.com/watch?v=o-Kz7suDYXE',
                 'https://cdn.discordapp.com/attachments/1052554161247486022/1052554161360752670/ooomeme.png?ex=67ccd8b3&is=67cb8733&hm=77058ce38a8b829f5306596c4378aa85b916232ee8dccd621c71c7fee47d99f8&',
                 'https://cdn.discordapp.com/attachments/967165979870236732/970292304629858324/Minecraft__1.17_-___2021-06-21_21-03-52.mp4?ex=67ccd8e0&is=67cb8760&hm=24bcd7d9ac3e398974e6e232204bb00b808515686209c1125366a3f0dfb532e1&',
                 'https://cdn.discordapp.com/attachments/1236673315146301480/1347574003551965206/image.png?ex=67ccfa57&is=67cba8d7&hm=ca8ac2f60377eba7439becbf347695f6154a70b271aa1837c75068a109bd5bbb&',
                 'https://cdn.discordapp.com/attachments/967091313038196799/967555498427691008/IMG_20220424_013929.jpg?ex=67ccc747&is=67cb75c7&hm=c973a4c26ed6da659bc2a78f7b12a8afaf9b8dc7ebd4121fd316d7df8dfe3e7a&',
                 'https://cdn.discordapp.com/attachments/967091313038196799/985660594776604672/2022-06-13_00.21.41.png?ex=67ccb9f6&is=67cb6876&hm=00c91abc5c24684a410472a3354072ecae208bb2e410fa21e0c527f53e437f8e&',
                 'https://cdn.discordapp.com/attachments/967091313038196799/983821042835394660/unknown.png?ex=67cca03f&is=67cb4ebf&hm=f6fb9bdfed29f7db74516c8d9bf2b0d200252f806757293f2d571ee097f8b818&',
                 'https://cdn.discordapp.com/attachments/973855354242883614/988149740984205393/unknown.png?ex=67cc8da9&is=67cb3c29&hm=91f2b73d2c909bb82d027dfde6274f7eb99815dcad1144d29af49293aa1a533f&',
                 'https://cdn.discordapp.com/attachments/967091313038196799/986727094694326334/unknown.png?ex=67cca6b7&is=67cb5537&hm=836b8de365b81e97007333dc1cdc33c1b283c3dfca324e019fe3c31e4f89088b&',
                 'https://cdn.discordapp.com/attachments/967091313038196799/1004073870132772975/unknown.png?ex=67cd22e9&is=67cbd169&hm=57da359e97aba90c4f5fe280b743c878f70c057d82b90c0da70d1b92a56ec461&',
                 'https://cdn.discordapp.com/attachments/973855354242883614/993236278164328539/2022-07-03_20.51.41.png?ex=67cc99de&is=67cb485e&hm=778ef073e1f0cd64b6abba68f0fa10b192fa14ff8cf4a9219a4e00dbf7388118&',
                 'https://media.discordapp.net/attachments/973855354242883614/995735240104488970/2022-07-07_00.59.09.png?ex=67cd1f75&is=67cbcdf5&hm=731044107c6a807a29ae6d534068f59be4c42ac0e036bedcb2e4c14a87001a0c&=&format=webp&quality=lossless&width=1708&height=881',
                 'https://cdn.discordapp.com/attachments/967091313038196799/1042569919386107966/image.png?ex=67ccc766&is=67cb75e6&hm=4aa89dee5385f99ad9da4923cc5f973bdbf8d7bd89e0d94b3096051b08779fa0&',
                 'https://cdn.discordapp.com/attachments/1053245957808070656/1053245958235902012/unknown_7.png?ex=67ccb9fc&is=67cb687c&hm=1a21aea8f75771c265e2b1321397e57d2cf828091929ca8bda20080f2fcc85b5&',
                 'https://cdn.discordapp.com/attachments/967091313038196799/1051924028794863777/image.png?ex=67cc8818&is=67cb3698&hm=5383778cd503a109ec36291769daec85c015e937da92117ce3ddfc7aef127f2c&',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1057312190962610227/unknown_1672153136569.png?ex=67cd0476&is=67cbb2f6&hm=50323c2d9777b362055f02908925b34f36edda71b0c8657943c4158383cbf1cb&',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1055105492202033212/94cef12ad874169a.gif?ex=67cce650&is=67cb94d0&hm=3160a5941df23b5c56683231405db5d64b528d976d9c568f4cf34df1f12ca3ed&',
                 'https://media.discordapp.net/attachments/1058470259872518204/1058470260803653754/2022-12-30_21.35.02.png?ex=67cc9dbf&is=67cb4c3f&hm=3d329aaf17bb0ea212b85ce83cf63a33b5b655249e4f5f1405a9b04c9cd1ca90&=&format=webp&quality=lossless&width=1708&height=881',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1063512171293720718/2023-01-09_01.16.41.png?ex=67cd2924&is=67cbd7a4&hm=eb48612a63ad8f09525b24f62c900e929ed6e077d51956a57d6d0cfad9123759&',
                 'https://cdn.discordapp.com/attachments/973855354242883614/1064904808215085096/caption-3.gif?ex=67ccf423&is=67cba2a3&hm=49962465f554cd00058178c749809c0f6c2e1ca6ae0b9f6a1b3a17b05a7c77eb&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1067036219139162122/IMG_20230123_140035.jpg?ex=67cccc2b&is=67cb7aab&hm=077ff62e90cf1b168af2d7f44b5c918a3ee3eb4816a671d25861cc42f382b2e3&',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1069039172146430062/image.png?ex=67ccd550&is=67cb83d0&hm=8e04d568ed748cd35512bab24fa5c6b7faef45f98b65dc8529cb4448e5dc466f&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1068543204389032067/2022-05-15_18.png?ex=67cd01a8&is=67cbb028&hm=4f9b4335aa91c53874a58f31b605a553fe0bf0f1c839accbb99f88bc0cef39af&',
                 'https://cdn.discordapp.com/attachments/973855354242883614/1070045755236167680/IMG_20230131_211925.jpg?ex=67cc8a44&is=67cb38c4&hm=ec8e711eb3f5d16985ec1ee778480ee8d0a3f8cad3140778e864c96288764fef&',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1074406524526534808/image.png?ex=67cc958c&is=67cb440c&hm=257f133c45c9b81c26071638dd587708c1b5992ea8bf086ade7b272bea401fa8&',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1075127851386425405/image.png?ex=67cc9256&is=67cb40d6&hm=82ddfb5663ea278a201baf7d4d78b29b5e65a708b5ee01ba22c5bffeb1d38931&',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1080147544346202275/image.png?ex=67cd090a&is=67cbb78a&hm=8c140a13688d3008437fc02cebf6a35f884a51714a0f013f8d126b16e5d72f2e&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1081255204395159643/image.png?ex=67cd1c21&is=67cbcaa1&hm=1110ffe02823f5e114de5036481e65ab56903ada9fed14892a18acf53e9edc2d&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1081260176537047200/image.png?ex=67cd20c2&is=67cbcf42&hm=d5bb5c3cecb1f0f825d7c2647bd8506411357db5bc01585e67c55949283b9a96&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1093821298171453450/566535385_456239226.mp4?ex=67ccaeb7&is=67cb5d37&hm=ddd3258f42517ef49795faeadf0c48fd45ad5e2d66ec30e9018fb2ee0c09505e&',
                 'https://cdn.discordapp.com/attachments/1052159403584913428/1098346753939492925/image.png?ex=67ccaaa0&is=67cb5920&hm=32a24682c965cb92a14c029368fb82642635bf557adaae2f615ea6a66a5abec5&',
                 'https://cdn.discordapp.com/attachments/1052159403584913428/1111429447820791878/image.png?ex=67ccccd5&is=67cb7b55&hm=e6ce3c7114697abb1d7d501c23d401e590bc49524971e10194f5e04776d9fb52&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1093914717715693659/image.png?ex=67cd05b8&is=67cbb438&hm=fdfe5357b5d36e5ccc61cbf3b0425568c91ffde7a47a228c68ed33d13000edf6&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1093914657414193303/image.png?ex=67cd05aa&is=67cbb42a&hm=5167ff6c852dc85736772912498f1de7e8ebad306603bc24c98d71e35966e3f9&',
                 'https://cdn.discordapp.com/attachments/973855354242883614/1114576467167297636/IMG_20230603_180347.jpg?ex=67cd0af9&is=67cbb979&hm=72d0c6293e7ac57fefc77b4dc5cd3023a5dc570fe19aaaa199e9c45468808dba&',
                 'https://cdn.discordapp.com/attachments/973855354242883614/1113603484500099122/image.png?ex=67cccc90&is=67cb7b10&hm=5d8ff32583ebfdfac83a8f796e72836261774bd6cf798cfb31e3d57a38e279a5&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1113575593636798574/image.png?ex=67ccb296&is=67cb6116&hm=6783cb181a035ade67963207175ef0c8b748834df41b2cf44b2408dcf36643b1&',
                 'https://cdn.discordapp.com/attachments/1115735315525672980/1115740961897726063/2022-11-17_20.10.56.png?ex=67ccaa3e&is=67cb58be&hm=4875380611634577692ac7b22e0a65b4d9ad6f774c1b430f19dedac8a1a17771&',
                 'https://cdn.discordapp.com/attachments/1115735315525672980/1115739013744173077/2022-06-08_19.57.57.png?ex=67cca86e&is=67cb56ee&hm=89aa3a612d1d60da3381ce7a735ec4a6e6ae84cc322f52704165244c14876104&',
                 'https://discord.com/channels/967091313038196796/1115735315525672980/1115738891597651968',
                 'https://cdn.discordapp.com/attachments/1115735315525672980/1115737126923944138/2022-04-25_19.49.02.png?ex=67cca6ac&is=67cb552c&hm=4a260b6a9440bd60b2180e898df842369523dedf455189e7b9dbcbbb9febab99&',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1133723612185116682/IMG_20230726_163236.jpg?ex=67ccd3a4&is=67cb8224&hm=a54fd3d9d432667d3b5a293e34642166b1aee6bcc5ecb0389f3498c9cd9fdbb6&',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1134892521558913155/image.png?ex=67cd1fc6&is=67cbce46&hm=facdace071ec82728b1530294a5188f2a7133c538bc1f23299703b860979a767&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1154808442603712553/image.png?ex=67cd116c&is=67cbbfec&hm=848e67876d4682aa96d16dc4d8078c3a0e8251017edcb8f3d67c1b10b5ad85b0&',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1153014381756555305/nakurilsa2.png?ex=67cd2212&is=67cbd092&hm=5b91dad4e5191b00e467fd852b3949fa1acfbe293cb17c2e65c40944d92f5e57&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1156561238885666916/IMG_20230927_150045.jpg?ex=67ccda57&is=67cb88d7&hm=9bfa1f73d3e47735a38ecb31a240c00db6c6bab2fff51045c98b1bd41acce6ed&',
                 'https://cdn.discordapp.com/attachments/1027313548315086878/1160709997370544220/tiny-nerd.gif?ex=67ccc8ec&is=67cb776c&hm=6686345c1acb12b7ba995a825857704914c3692f9ea3942bdf10c37a0e2fd748&',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1160684305496932484/area_render.png?ex=67ccb0fe&is=67cb5f7e&hm=8143d3b200c855fb56f3b96fbb85298080f728e98ef78a87beae2047a1c9a87d&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1168834219053678602/1168833142610743377remix-1698742188237.png?ex=67ccad71&is=67cb5bf1&hm=522b9da0cc16b16c9e0b566e851d1943fef5c3ef6ec0b433342ab4e2f7140bb2&',
                 'https://tenor.com/view/%D0%B4%D0%BE%D0%B2%D0%BE%D0%B4-tenet-christopher-nolan-nolan-%D0%BE%D0%B1%D1%81%D1%83%D0%B6%D0%B4%D0%B0%D0%B5%D0%BC-gif-24881957',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1184878465833508934/image.png?ex=67cd09d0&is=67cbb850&hm=7e549305345b4cb675c0feb1951c47e7b37fe0e5d94d75932d7c31977ef3054b&',
                 'https://cdn.discordapp.com/attachments/1051934380924338186/1195773410685493321/image.png?ex=67cd1f85&is=67cbce05&hm=d1867ce3b884e21eeefea2907e6563e54bf75ee528b491cb9ff2b3871df8068c&',
                 'https://cdn.discordapp.com/attachments/1109099791419457627/1197499975526006825/IMG_20240118_141158_874.jpg?ex=67ccd002&is=67cb7e82&hm=dfda079a68b731ff00a1e53220fa10234077941d0849a0f60769dc6023526fa6&',
                 'https://tenor.com/view/gorilla-reaction-gorilla-shocked-appauled-eating-pepper-gif-2230596277954293584',
                 'https://cdn.discordapp.com/attachments/1042878735965245512/1200698743687761920/image.png?ex=67cc9598&is=67cb4418&hm=db5c3e6f3188056cf96371f8398c6e8dc852546d0cc0d93efab08741197b727f&']
        await ctx.send(random.choice(links))

    @commands.command()
    async def help(self, ctx, command: str = None, member: discord.Member = None):
        LANG = f"LANG_{servers_ref.child(str(ctx.guild.id)).child("LANGUAGE").get()}"
        if member == None:
            member = ctx.author

        name = member.display_name
        pfp = member.display_avatar

        commands_gamenight = {
            "gamenight_start": {
                'LANG_RU': [
                "```Команда создаёт ивент Геймнайт (только админы могут использовать эту команду). При создании ивента появится сообщение бота с кнопкой, нажав которую можно будет предложить от 1 до 3 игр. Выбор игры в которую захочется поиграть происходит вручную (через какие-нибудь сайты с рулетками)```",
                None,
                {"/gamenight_start": "Запускает Геймнайт"},
                None],
                'LANG_EN': [
                "```This command creates a Game Night event (only admins can use this command). When creating an event, a bot message will appear with a button that allows you to offer from 1 to 3 games. The game you want to play is selected manually (through some random wheel sites)```",
                None,
                {"/gamenight_start": "Starts the Game Night event"},
                None]
            },
            "gamenight_list": {
                'LANG_RU': ["```Посмотреть список предложенных игр для Геймнайта и возможность скачать json-file```",
                            None,
                            {"/gamenight_list": "Показывает список игр, с приложением в виде файла-json"},
                            None],
                'LANG_EN': ["```View the list of suggested games for Game Night event and the ability to download a json-file```",
                            None,
                            {"/gamenight_list": "Shows a list of games with the application of a json-file."},
                            None],
            },
            "gamenight_end": {
                'LANG_RU': ["```Команда закрывает предложение игр для Геймнайта и сам ивент (админы могут только)```",
                            None,
                            {"/gamenight_end": "Объявляет конец Геймнайта"},
                            None],
                'LANG_EN': ["```This command closes the ability of suggesting games for Game Night event and the event itself (only admins can)```",
                            None,
                            {"/gamenight_end": "Announces the end of Game Night event"},
                            None],
            },
            "gamenight_gamedelete": {'LANG_RU': ["```Удалить СВОЮ игру из списка предложенных игр Геймнайта.```",
                                                 {"[suggestion]": "Предложенная вами игра в списке игр."},
                                                 {
                                                     "/gamenight_gamedelete `suggestion:game1`": "Команда удаляет из списка игр вашу игру `game1`"},
                                                 None],
                                     'LANG_EN': ["```Remove YOUR suggested game from the list of Game Night event's games.```",
                                                 {"[suggestion]": "The game you suggested in the list of event's games."},
                                                 {
                                                     "/gamenight_gamedelete `suggestion:game1`": "This command removes your suggested game `game1` from the list of event's games"},
                                                 None]
                                     }
        }
        commands_rpg = {
            "profile": {
                'LANG_RU': [
                "```Команда показывает вам персонажа и открывает ваш инвентарь, где показывается баланс (монетки), вещи (если имеются). При наличии нескольких страниц инвентаря, их можно листать с помощью кнопок```",
                None,
                {"!profile": "Показывает вашего персонажа и проверяет свой карман (на наличие денег или предметов)",
                 "!profile @user": "Показывает чужого персонажа и проверяет чужой карман через упоминание пользователя (на наличие денег или предметов)",
                 "!balance 123456789": "Показывает чужого персонажа и проверяет чужой карман через ID пользователя (на наличие денег или предметов)"},
                {"[user]": "Упоминание (@user) или же его числовое ID"}
                ],
                'LANG_EN': [
                "```This command shows your playable character and opens your inventory (pocket), which shows the balance (coins), items (if you have any). If you have several inventory pages, you can scroll through them using the buttons```",
                None,
                {"!profile": "Shows your playable character and checks your pocket (for money or items)",
                 "!profile @user": "Shows someone else's character and checks someone else's pocket through the user mention (for money or items)",
                 "!balance 123456789": "Shows someone else's character and checks someone else's pocket through the user ID (for money or items)"},
                {"[user]": "A mention (@user) or his numeric ID"}
                ]
            },

            "fish": {
                'LANG_RU': ["```Рыбалка симулятор```",
                                 None,
                                 {"!fish": "Команда запускает мини-игру рыбалку. Чтобы пройти эту мини-игру, нужно нажимать на кнопки (вверх, вниз, влево, вправо) и дойти до какой-либо рыбы или предмета. Таким образом вы поймаете что-то."},
                                 None],
                'LANG_EN': ["```Fishing Simulator```",
                                 None,
                                 {"!fish": "This command launches a fishing mini-game. To complete this mini-game, you need to press the buttons (up, down, left, right) and reach any fish or object. This way you will catch something."},
                                 None]
            },
            "sell": {
                'LANG_RU': ["```Команда позволяет продать предмет или весь ваш инвентарь```",
                                 {"[:emoji:]": "Эмодзи, например 🐟",
                                  "[inventory]": "Слово inventory даст вам продать весь ваш инвентарь"},
                                 {"!sell 🍌": "Команда продаст банан из вашего инвентаря (если он есть). Если у вас много предметов, можно указать `индекс`, например 1 или 2, или же слово `всё`, чтобы продать все предметы данного вида",
                                  "!sell inventory": "Команда продаст весь ваш инвентарь"},
                                 None],
                'LANG_EN': ["```This command allows you to sell an item or your entire inventory.```",
                                 {"[:emoji:]": "Emoji, for example 🐟",
                                  "[inventory]": "The word inventory itself will let you sell your entire inventory"},
                                 {"!sell 🍌": "This command will sell a banana from your inventory (if there is one). If you have a lot of items, you can specify an `index`, such as 1 or 2, or the word `all` to sell all items of this type.",
                                  "!sell inventory": "This command will sell your entire inventory"},
                                 None]
            },
            "leaderboard": {
                'LANG_RU': [
                "```Просмотр локальной или глобальной таблицы монет. В выпадающем списке необходимо выбрать уровень просмотра (локальный или глобальный)```",
                None,
                {"/leaderboard": "Команда показывает выбранный лидерборд"},
                None],
                'LANG_EN': [
                "```View the local or global leaderboard of coins. In the drop-down list, select the viewing level (local or global)```",
                None,
                {"/leaderboard": "This command shows the selected leaderboard"},
                None]
            },
            "shop": {
                'LANG_RU': ["```Просмотр магазина, который обновляется каждые 6 часов.```",
                                 None,
                                 {"!shop": "Команда показывает меню магазина"},
                                 None],
                'LANG_EN': ["```View the shop, which is updated every 6 hours.```",
                                 None,
                                 {"!shop": "This command shows the shop's menu"},
                                 None]
            },
            "craft": {
                'LANG_RU': [
                "```Команда создает предмет, если рецепт (те эмодзи, которые вы отправили) окажется верным.```",
                {"[:emoji1:]": "Первый эмодзи, например 🐟", "[:emoji2:]": "Второй эмодзи, например 🐡"},
                {"!craft 🐟🐡": "Команда может быть скрафтит что-то из двух предметов!",
                 "!craft 🎩🍌👢": "Команда может быть скрафтит что-то из трёх предметов!"},
                {"[:emoji3:]": "Третий эмодзи, например 🎩"}
                ],
                'LANG_EN': [
                "```This command creates an item if the recipe (the emojis you sent) turns out to be correct.```",
                {"[:emoji1:]": "The first emoji, for example 🐟", "[:emoji2:]": "The second emoji, for example 🐡"},
                {"!craft 🐟🐡": "This command may craft something from two items!",
                 "!craft 🎩🍌👢": "This command may craft something from three items!"},
                {"[:emoji3:]": "The third emoji, for example 🎩"}
                ]
            },
            "pin": {
                'LANG_RU': [
                "```Команда позволяет пригвоздить предмет, чтобы его невозможно было продать, или наоборот, отгвоздить его, чтобы его можно было продать.```",
                {"[:emoji:]": "Эмодзи, например 🍌"},
                {
                    "!pin 🍌": "Команда пригвоздит предмет, чтобы его было нельзя продать. Если у вас много предметов, можно указать `индекс`, например 1 или 2, или же слово `всё`, чтобы пригвоздить все предметы",
                    "!pin 📌🐟": "Команда отгвоздит предмет, чтобы его можно было продать. Если у вас много предметов, можно указать `индекс`, например 1 или 2, или же слово `всё`, чтобы отгвоздить все предметы"},
                None],
                'LANG_EN': [
                "```This command allows you to pin an item so that it cannot be sold, or vice versa, to unpin it so that it can be sold.```",
                {"[:emoji:]": "Emoji, for example 🍌"},
                {
                    "!pin 🍌": "This command will pin the item so that it cannot be sold. If you have a lot of items, you can specify an `index`, such as 1 or 2, or the word `all` to pin all the items.",
                    "!pin 📌🐟": "The team will unpin the item so that it can be sold. If you have a lot of items, you can specify an `index`, such as 1 or 2, or the word `all` to label all items."},
                None]
            },
            "info": {
                'LANG_RU': [
                "```Команда позволяет узнать некоторую информацию о предмете, находящегося в вашем инвентаре. Показывает название предмета, дату получения и краткую информацию.```",
                {"[:emoji:]": "Эмодзи, например 🐟"},
                {"!info 🐟": "Команда покажет информацию об этом предмете, если он есть у вас в инвентаре."},
                None],
                'LANG_EN': [
                "```This command allows you to find out some information about an item in your inventory. Shows the name of the item, the date item was received, and brief information.```",
                {"[:emoji:]": "Emoji, for example 🐟"},
                {"!info 🐟": "This command will show information about this item if you have it in your inventory."},
                None]
            },
            "use": {
                'LANG_RU': ["```Команда позволяет использовать указанный предмет в вашем инвентаре.```",
                                {"[:emoji:]": "Эмодзи, например 👢"},

                                {
                                    "!info 👢": "Команда использует этот предмет и если у него есть применение (не все предметы можно использовать), то что-то произойдёт."},
                                None],
                'LANG_EN': ["```This command allows you to use the specified item in your inventory..```",
                                {"[:emoji:]": "Emoji, for example 👢"},

                                {
                                    "!info 👢": "This command uses this item and if it has a use (some items don't have any usage), then something may happen."},
                                None]
            },
            "location": {
                'LANG_RU': ["```Сердце РПГ сегмента бота. На данный момент команда позволяет просматривать текущую локацию, разговаривать с нпс, получать квесты от нпс.```",
                                 None,
                                 {"/location": "Команда видна только вам, вы можете просмотреть текущую локацию, поговорить с доступными нпс."},
                                 None],
                'LANG_EN': ["```The heart of the RPG segment of the bot. Currently, this command allows you to view the current location, talk to NPCs, and receive quests from NPCs.```",
                                 None,
                                 {"/location": "This command is visible to you only, you can view the current location, talk to the available NPCs."},
                                 None]
            }
        }
        commands_admin = {
            "cage": {
                'LANG_RU': [
                "```Команда позволяет отправить человека в подобие таймаута. Для использования этой команды необходимо настроить в /settings следующие параметры: TIMEOUT_CHANNEL_ID - айди канала, который будет доступен людям с таймаутом, TIMEOUT_ROLE_ID - роль, которая будет даваться людям с таймаутом. Вы сами выставляете ограничения у роли и у канала. По задумке, команда на время отправляет пользователя в специальный канал, чтобы тот подумал о своём поведении (или до тех пор, пока он не почистит N количество бананов, но это опционально).```",
                {"[@юзер]": "Упоминание пользователя",
                 "[s/m/h/d]": "Время, например 50s или 20d или 3h (50 секунд или 20 дней или 3 часа)."},
                {"!cage member:@dummy#9470 time:5s": "Команда отправит участника @dummy#9470 в таймаут на 5 секунд.",
                 "!cage member:@dummy#9470 time:3d bananas:50": "Команда отправит участника @dummy#9470 в таймаут на 3 дня, НО он может выбраться досрочно, если почистит 50 бананов.",
                 "!cage member:@dummy#9470 time:5s reason:ну отдохни на водах": "Команда отправит участника @dummy#9470 в таймаут на 5 секунд, также в сообщении будет указана причина отправки в таймаут."},
                {
                    "[бананы]": "Количество бананов, которое необходимо почистить, чтобы досрочно выбраться из таймаута. Например 50.",
                    "[причина]": "Текст причины, за которую пользователь отправлен в таймаут (в том числе пользователю будет видно, кто отправил в таймаут)"
                }
                ],
                'LANG_EN': [
                "```The command allows you to send a person to a some kind of timeout. To use this command, you need to configure the following parameters in /settings: TIMEOUT_CHANNEL_ID - the ID of the channel that will be available to people with a timeout, TIMEOUT_ROLE_ID - the role that will be given to people with a timeout. You set the limits and permissions for the role and the channel yourself. Ideally, this command temporarily sends the user to a special channel so that user thinks about theirs behavior (or until user peels N quantity of bananas, but this is optional).```",
                {"[@user]": "User Mention",
                 "[s/m/h/d]": "Time, for example, 50s or 20d or 3h (50 seconds or 20 days or 3 hours)."},
                {"!cage member:@dummy#9470 time:5s": "This command will send user @dummy#9470 to a 5-second timeout.",
                 "!cage member:@dummy#9470 time:3d bananas:50": "This command will send user @dummy#9470 to a 3-day timeout, BUT user can be released early if user peels 50 bananas..",
                 "!cage member:@dummy#9470 time:5s reason:go chill dude": "This command will send user @dummy#9470 to a timeout for 5 seconds and the reason for the timeout will also be included in the message."},
                {
                    "[bananas]": "The number of bananas that need to be peeled in order to get out of the timeout early. For example 50.",
                    "[reason]": "The reason why the user was timed out (they will also see who timed them out)."
                }
                ]
            },
            "settings": {
                'LANG_RU': [
                "```Команда позволяет настроить бота (нужные айди каналов и ролей). Следующие поля можно настроить:\nBOT_CHANNEL_ID - Канал, где бот будет отправлять некоторые сообщения-оповещения (если это необходимо некоторым командам, данный айди пока что используется только в команде /gamenight_start, смотрите help по ней)\nPREFIX - Префикс бота. Сейчас недоступен.\nTIMEOUT_CHANNEL_ID - Канал для таймаутов. По задумке (вы можете сделать иначе) в этот канал должна иметь доступ только одна роль, она может туда писать, но не может просматривать остальные каналы вашего сервера (Канал используется в команде /cage, смотрите help по ней).\nTIMEOUT_ROLE_ID - Роль, которая имеет доступ к ранее упомянутому каналу, по сути таймаут-роль (выдаётся пользователям с помощью команды /cage, смотрите help по ней).\nLANGUAGE - Язык, на котором будет отвечать бот. Доступен `RU`, `EN` ```",
                None,
                {"/settings": "Команда запускает меню настройки."},
                None],
                'LANG_EN': [
                "```This command allows you to configure the bot (required channel and role IDs). The following fields can be configured:\nBOT_CHANNEL_ID - The channel where the bot will send certain notification messages (if required by some commands; this ID is currently only used by the `/gamenight_start` command, see its help for more details).\nPREFIX - The bot's command prefix. Currently unavailable\nTIMEOUT_CHANNEL_ID - The channel for timeouts. The idea (you can set it up differently) is that only one specific role should have access to this channel. This role can write in it but cannot view the rest of your server's channels (this channel is used by the `/cage` command, see its help for more details).\nTIMEOUT_ROLE_ID - The role that has access to the aforementioned channel — essentially, the timeout role (assigned to users via the `/cage` command, see its help for more details).\nLANGUAGE - The language the bot will respond in. `RU`, 'EN` are available.```",
                None,
                {"/settings": "This command shows the settings menu."},
                None]},
        }

        commands_other = {
            "feedback": {
                'LANG_RU': [
                "```Команда отправляет фидбек о боте (ваши идеи, впечатления и так далее). Создатель бота может ответить на сообщение.```",
                {"[текст]": "Текст, который отправится создателю бота."},
                {
                    "!feedback ну короче жду бесплатный бургер": "Команда отправит сообщение 'ну короче жду бесплатный бургер' создателю бота. Он сможет ответить на ваше сообщение."},
                None],
                'LANG_EN': [
                "```This command sends feedback about the bot (your ideas, impressions, and so on). The creator of the bot may reply to the message.```",
                {"[text]": "The text that will be sent to the creator of the bot."},
                {
                    "!feedback urm give me a free cheeseburger": "This command will send a message 'urm give me a free cheeseburger' to the creator of the bot. He may reply to your message."},
                None]
            },

            "meme": {
                'LANG_RU': ["```Команда отправляет рандомный мем из коллекции локальных мемов.```",
                                 None,
                                 {"!meme": "Отправляет рандомный мем из коллекции."},
                                 None],
                'LANG_EN': ["```This command sends a random meme from the collection of local memes.```",
                                 None,
                                 {"!meme": "Sends a random meme from the collection."},
                                 None]
            },
            "test": {
                'LANG_RU': ["```Команда повторяет за пользователем всё, что он напишет.```",
                                 {"[сообщение]": "Текст, который вы напишите."},
                                 {"!test привет": "Бот отправит сообщение 'привет'.",
                                  "/test arg:привет": "Бот отправит сообщение 'привет'."},
                                 None],
                'LANG_EN': ["```This command repeats everything the user writes.```",
                                 {"[message]": "The text that you wrote."},
                                 {"!test hello": "The bot will send a message 'hello'.",
                                  "/test arg:hello": "The bot will send a message 'hello'."},
                                 None]
            },
            "help": {
                'LANG_RU': ['```Команда, которая рассказывает о назначении команды "помощи"```',
                                 None,
                                 {
                                     "!help settings": 'Бот отправит сообщение, в котором содержится подробная информация о команде "settings".'},
                                 {"[команда]": "Команда, которую вы хотите подробно изучить."}
                            ],
                'LANG_EN': ['```A command that explains the purpose of the "help" command.```',
                                 None,
                                 {
                                     "!help settings": 'The bot will send a message that contains detailed information about the "settings" command.'},
                                 {"[command]": "The command you want to be explained in detail."}
                ]
            }
        }

        commands_minigames = {
            "bikeshot":
                {'LANG_RU': ["```Команда запускает игру `bikeshot`.```",
                                                        None,
                                                       {"!bikeshot": "Команда запускает игру `bikeshot`. Принцип игры прост - Вы играете против Байкера, вам нужно выиграть."},
                                                        None],
                'LANG_EN': ["```This command launches a mini-game `bikeshot`.```",
                                                        None,
                                                       {"!bikeshot": "This command starts the mini-game `bikeshot'. The idea of the game is simple - You are playing against a Biker and you need to win."},
                                                        None]
            },

        }

        if command is None:
            embed = discord.Embed(title=f'{ui_localization.get("help").get("help_standard_commands").get(LANG)}',
                                  colour=discord.Colour(int('a970ff', 16)))
            embed.set_author(name=f"{ui_localization.get("help").get("help_dimabot").get(LANG)} ft. {member.guild.name}", icon_url="https://imgur.com/T9qLfHj.png")

            embed.add_field(name=f"{ui_localization.get("help").get("help_gamenight").get(LANG)}", value=f"{str("".join([f"`{i}`\n" for i in commands_gamenight.keys()]))}",
                            inline=True)
            embed.add_field(name=f"{ui_localization.get("help").get("help_economy").get(LANG)}", value=f"{str("".join([f"`{i}`\n" for i in commands_rpg.keys()]))}",
                            inline=True)
            embed.add_field(name=f"{ui_localization.get("help").get("help_mod").get(LANG)}", value=f"{str("".join([f"`{i}`\n" for i in commands_admin.keys()]))}",
                            inline=True)
            embed.add_field(name=f"{ui_localization.get("help").get("help_other").get(LANG)}", value=f"{str("".join([f"`{i}`\n" for i in commands_other.keys()]))}",
                            inline=True)
            embed.add_field(name=f"{ui_localization.get("help").get("help_games").get(LANG)}", value=f"{str("".join([f"`{i}`\n" for i in commands_minigames.keys()]))}",
                            inline=True)

            view = Menu()
            view.add_item(
                discord.ui.Button(label='Twitch Channel', style=discord.ButtonStyle.link,
                                  url='https://www.twitch.tv/mrtomit'))
            await ctx.send(embed=embed, view=view)
        else:
            new_command = command.replace("/", "").replace("!", "")
            parse_ = [commands_gamenight, commands_rpg, commands_admin, commands_other, commands_minigames]
            for i, d in enumerate(parse_, 1):
                if new_command in d:
                    embed = discord.Embed(title=f'{command}', description=f"{d[new_command][LANG][0]}")
                    if not (d[new_command][LANG][1] is None):
                        embed.add_field(name=f"{ui_localization.get("help").get("help_params_required").get(LANG)}:",
                                        value=f"{str("".join([f"`{i} -- {j}`\n" for i, j in d[new_command][LANG][1].items()]))}",
                                        inline=False)
                    if not (d[new_command][LANG][3] is None):
                        embed.add_field(name=f"{ui_localization.get("help").get("help_params_required").get(LANG)}:",
                                        value=f"{str("".join([f"`{i} -- {j}`\n" for i, j in d[new_command][LANG][3].items()]))}",
                                        inline=False)
                    embed.add_field(name=f"{ui_localization.get("help").get("help_usage_example").get(LANG)}:",
                                    value=f"{str("".join([f"{i}\n{j}\n\n" for i, j in d[new_command][LANG][2].items()]))}",
                                    inline=False)
                    embed.set_author(name=f"{ui_localization.get("help").get("help_dimabot_helper").get(LANG)}")
                    await ctx.send(embed=embed)
                    return
            await ctx.send(f"{ui_localization.get("help").get("help_no_command").get(LANG)}")

async def setup(client):
    await client.add_cog(OtherCog(client))