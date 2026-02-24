import json
import os
import random


import firebase_admin

from firebase_admin import db, credentials


"""
Gaming
"""

active_games = {}

"""
Env Variables и прочие вещи (базы данных)
"""

WELCOME_MESSAGE_EN = "Hello! it looks like ur trying to install dimabot on your server (or someone is trying to), however, itz not working properly yet vro... owner or any admin should probably configure bot's settings with a command `/settings`\ncheers!"
FEEDBACK_CHANNEL_ID = os.environ['FEEDBACK_CHANNEL_ID'] # ID канала с обратной связью.
PREFIX = '!'

service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
service_account_dict = json.loads(service_account_json)
cred = credentials.Certificate(service_account_dict)
firebase_admin.initialize_app(cred, {
      'databaseURL': f'{os.getenv("LINK_DATABASE")}'
  })

nights_ref = db.reference('nights')
economy_ref = db.reference('economy')
inventory_ref = db.reference('inventory')
penalty_ref = db.reference('penalty')
servers_ref = db.reference('servers')
rpg_stuff_ref = db.reference('rpg')

cool_dict = {}

'''
Секция со словарём предметов
Формат: Множитель, слово, название предмета, описание предмета, функция использования, эмодзи предмета, стандартная цена в магазине;
'''

all_items = {
    '👢': {
        "item_name": {'LANG_RU': "грязный ботинок", 'LANG_EN': "dirty boot"},
        "multiplier_price": lambda: round((random.random() + 1), 5),
        "description": {'LANG_RU': "Грязные ботинки штамповали тысячами в Австралии. Неизвестно почему, но все они оказались в море. Спасите морской биоценоз — соберите их все!",
                        "LANG_EN": "can't have these in yo oceans. save the planet — collect them all!"},
        "usage": "id0use",
        "shop_price": eval("round(6 * round(random.uniform(1,2), 1), 5)")
    },
    '🐚': {
        "item_name": {'LANG_RU': "плавающая ракушка", 'LANG_EN': "sea shell (swimming)"},
        "multiplier_price": lambda: round((random.random() + 1.21), 5),
        "description": {'LANG_RU': "Говорят, что через такие можно услышать море. Хотя, мы итак рядом с морем, чтобы его слушать.",
                        "LANG_EN": "They say you can hear the ocean through these things. Although we already have the ocean nearby"},
        "usage": "id0use",
        "shop_price": eval("round(48 * round(random.uniform(1,2), 1), 5)")
    },
    '🍌': {
        "item_name": {'LANG_RU': "банано", 'LANG_EN': "le banana"},
        "multiplier_price": lambda: round((random.random() + 1), 9),
        "description": {'LANG_RU': "Кто-то небрежно очистил банан от кожуры. Интересно, их действительно собирают с пальм?",
                        "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(25 * round(random.uniform(1,2), 1), 5)")
    },
    '🤖': {
        "item_name": {'LANG_RU': "петя умный", 'LANG_EN': "p3tya smart"},
        "multiplier_price": lambda: round((random.random() + 5.1), 9),
        "description": {'LANG_RU': "Петя версия v1. Ничего не делает. Зато круто выглядит.",
                        "LANG_EN": "p3tya version 1.0. Does nothing, but looks cool."},
        "usage": None,
        "shop_price": eval("round(20000 * round(random.uniform(1,2), 1), 5)")
    },
    '💩': {
        "item_name": {'LANG_RU': "мусор (говно)", 'LANG_EN': "junk (poop)"},
        "multiplier_price": lambda: round((random.random() + 1), 9),
        "description": {'LANG_RU': "Ну и что за хрень...",
                        "LANG_EN": "what the crap"},
        "usage": None,
        "shop_price": eval("round(2 * round(random.uniform(1,2), 1), 5)")
    },
    '🎩': {
        "item_name": {'LANG_RU': "шляпникус", 'LANG_EN': "Pooryhatitator"},
        "multiplier_price": lambda: round((random.random() + 2.45), 9),
        "description": {'LANG_RU': "Я не знаю, что это, но это точно не из нашего мира. Может быть, оно обладает каким-либо функционалом? Или используется для чего-то? Кто знает...",
                        "LANG_EN": "This thing is definitely doesn't belong to our world. Still, it must have an interesting usability"},
        "usage": None,
        "shop_price": eval("round(872 * round(random.uniform(1,2), 1), 5)")
    },
    '🧦': {
        "item_name": {'LANG_RU': "грязные носки (братья грязного ботинка)", 'LANG_EN': "dirty socks (brothers of the dirty boot)"},
        "multiplier_price": lambda: round((random.random() + 1.05), 9),
        "description": {'LANG_RU': "Грязные носки не штамповали тысячами, однако, эти раритетные экземпляры никто не хочет покупать. Ну, кроме вас, если вы сюда нажали, увы.",
                        "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(98 * round(random.uniform(1,2), 1), 5)")
    },
    '🏵️': {
        "item_name": {'LANG_RU': "цветок муосотис", 'LANG_EN': "miosotis flower"},
        "multiplier_price": lambda: round((random.random() + 1.5), 9),
        "description": {'LANG_RU': "Прекрасный подарок на любое событие в жизни человека.",
                        "LANG_EN": "A very beautiful gift."},
        "usage": None,
        "shop_price": eval("round(367 * round(random.uniform(1,2), 1), 5)")
    },
    '♟️': {
        "item_name": {'LANG_RU': "пешка", 'LANG_EN': "pawn"},
        "multiplier_price": lambda: round((random.random() + 6), 9),
        "description": {'LANG_RU': f"Checkmate in {str(random.randint(2, 600))} moves",
                        "LANG_EN": f"Checkmate in {str(random.randint(2, 600))} moves"},
        "usage": None,
        "shop_price": eval("round(2009 * round(random.uniform(1,2), 1), 5)")
    },
    '🎣': {
        "item_name": {'LANG_RU': "удочка TIER 2", 'LANG_EN': "fishing rod TIER 2"},
        "multiplier_price": lambda: round((random.random() + 2), 9),
        "description": {'LANG_RU': "Теперь вы сможете рыбачить не руками с леской и крючком, а с удочкой и леской с крючком",
                        "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(1575 * round(random.uniform(1,2), 1), 5)")
    },
    '🚘': {
        "item_name": {'LANG_RU': "собственная тачка", 'LANG_EN': "your own car"},
        "multiplier_price": lambda: round((random.random() + 3.45), 9),
        "description": {'LANG_RU': "Check out my new гелик!",
                        "LANG_EN": "Зацени мой новый gelendvagen!"},
        "usage": None,
        "shop_price": eval("round(16650 * round(random.uniform(1,2), 1), 5)")
    },
    '🔩': {
        "item_name": {'LANG_RU': "металлолом декеинг", 'LANG_EN': "scrap from decaying"},
        "multiplier_price": lambda: round((random.random() + 0.23), 9),
        "description": {'LANG_RU': "Очень распространённый материал чтобы использовать его для создания разных штук...",
                        "LANG_EN": "A very common material to use in crafting things."},
        "usage": None,
        "shop_price": eval("round(250 * round(random.uniform(1,2), 1), 5)")
    },
    '📟': {
        "item_name": {'LANG_RU': "пейджер", 'LANG_EN': "scrap from decaying"},
        "multiplier_price": lambda: round((random.random() + 2.3), 9),
        "description": {'LANG_RU': "Прямиком из 1980-го года (ну это у нас).",
                        "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(487 * round(random.uniform(1,2), 1), 5)")
    },
    '🖲️': {
        "item_name": {'LANG_RU': "красная кнопка", 'LANG_EN': "red button"},
        "multiplier_price": lambda: round((random.random() + 2.1), 9),
        "description": {'LANG_RU': "У-у-у, прямо таки хочется нажать!",
                        "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(129 * round(random.uniform(1,2), 1), 5)")
    },
    '💰': {
        "item_name": {'LANG_RU': "мешок с деньгами", 'LANG_EN': "money bag"},
        "multiplier_price": lambda: round((random.random() + 1), 9),
        "description": {'LANG_RU': "Очень распространённый материал чтобы использовать его для создания разных штук...",
                        "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(5000000 * round(random.uniform(1,2), 1), 5)")
    },
    '🧬': {
        "item_name": {'LANG_RU': "ДНК", 'LANG_EN': "DNA"},
        "multiplier_price": lambda: round((random.random() + 5.3), 9),
        "description": {'LANG_RU': "Каким образом это вообще продаётся? Похоже, мы живём в будущем! Я сам определяю свой геном...",
                        "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(999 * round(random.uniform(1,2), 1), 5)")
    },
    '🪚': {
        "item_name": {'LANG_RU': "пилище", 'LANG_EN': "sawwy"},
        "multiplier_price": lambda: round((random.random() + 1.6), 9),
        "description": {'LANG_RU': "Я бы с такой не играл.",
                        "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(339 * round(random.uniform(1,2), 1), 5)")
    },
    '🚪': {
        "item_name": {'LANG_RU': "дверь", 'LANG_EN': "door"},
        "multiplier_price": lambda: round((random.random() + 1.28), 9),
        "description": {'LANG_RU': "Дверь мне запили",
                        "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(199 * round(random.uniform(1,2), 1), 5)")
    },
    '🍣': {
        "item_name": {'LANG_RU': "сашими", 'LANG_EN': "sashimi"},
        "multiplier_price": lambda: round((random.random() + 1.28), 9),
        "description": {'LANG_RU': "DIY, прямиком из-под ножа!",
                        "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(155 * round(random.uniform(1,2), 1), 5)")
    },
    '⛵': {
        "item_name": {'LANG_RU': "лодка", 'LANG_EN': "boat"},
        "multiplier_price": lambda: round((random.random() + 1.12), 9),
        "description": {'LANG_RU': "преследуешь мечты которые дрим и sail или просто ты лоцман - прямой путь в японию",
                        "LANG_EN": "placeholder"},
        "usage": "id26use",
        "shop_price": eval("round(2500 * round(random.uniform(1,2), 1), 5)")
    },
    '☎️': {
        "item_name": {'LANG_RU': "телефончик", 'LANG_EN': "scrap from decaying"},
        "multiplier_price": lambda: round((random.random() + 1.1189), 9),
        "description": {'LANG_RU': "Сломанный телефон",
                        "LANG_EN": "A broken phone."},
        "usage": None,
        "shop_price": eval("round(500 * round(random.uniform(1,2), 1), 5)")
    },

}

all_fish = {
    '🐟': {
        "item_name": {'LANG_RU': "карась", 'LANG_EN': "crucian"},
        "multiplier_price": lambda: round((random.random() + 1.1), 9),
        "description": {'LANG_RU': "Карась является самым частовречающимся представителем в здешних водах. Скажите ему привет!", "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(51 * round(random.uniform(1,2), 1), 5)")
    },
    '🐠': {
        "item_name": {'LANG_RU': "брат карася", 'LANG_EN': "crucian's brother"},
        "multiplier_price": lambda: round((random.random() + 1.45), 9),
        "description": {'LANG_RU': "Брат Карася не знает, что у него есть брат. Похоже, тот отбился от косяка... Какая досада!", "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(random.randint(27, 109) * round(random.uniform(1,2), 1), 5)")
    },
    '🐡': {
        "item_name": {'LANG_RU': "рыба агу ага", 'LANG_EN': "goo goo ga ga fish"},
        "multiplier_price": lambda: round((random.random() + 1.28), 9),
        "description": {'LANG_RU': "Это удивительная рыба Агу Ага, о ней мало что известно человечеству.", "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(62 * round(random.uniform(1,2), 2), 5)")
    },
    '🪼': {
        "item_name": {'LANG_RU': "медуза крутая", 'LANG_EN': "cool jellyfish"},
        "multiplier_price": lambda: round((random.random() + 1.76), 9),
        "description": {'LANG_RU': "Нередко медузы считаются крутыми, поскольку технически бессмертны (кроме того видоса про черепаху).", "LANG_EN": "placeholder"},
        "usage": None,
        "shop_price": eval("round(73 * round(random.uniform(1,2), 2), 5)")
    },
    '🦐': {
        "item_name": {'LANG_RU': "креветочка", 'LANG_EN': "shrimpy"},
        "multiplier_price": lambda: round((random.random() + 1.2), 9),
        "description": {'LANG_RU': "Эта креветочка такая милая :)", "LANG_EN": "this shrimpy be so cute :)"},
        "usage": None,
        "shop_price": eval("round(56 * round(random.uniform(1,2), 2), 5)")
    },
    '🐙': {
        "item_name": {'LANG_RU': "разрушитель три тысячи", 'LANG_EN': "THE_Destroyer_3000"},
        "multiplier_price": lambda: round((random.random() + 2.3), 9),
        "description": {'LANG_RU': "Ну, не такой уж и страшный.", "LANG_EN": "Well, actually, not that scary at all..."},
        "usage": None,
        "shop_price": eval("round(290 * round(random.uniform(1,2), 2), 5)")
    },
    '🦈': {
        "item_name": {'LANG_RU': "Я АКУЛА", 'LANG_EN': "I AM A SHARK"},
        "multiplier_price": lambda: round((random.random() + 3.23), 9),
        "description": {'LANG_RU': "ААААААААААА ЛАДНО", "LANG_EN": "OKAAAAAAAAY"},
        "usage": None,
        "shop_price": eval("round(430 * round(random.uniform(1,2), 2), 5)")
    },
}

full_items = all_items | all_fish

crafting_dict = {
            frozenset(['🪚', '🚪', '🔩']): full_items.get('🎣'),
            frozenset(['🧬', '📟', '🖲️']): full_items.get('🤖'),
            frozenset(['🎩', '📟', '🖲️']): full_items.get('🚘'),
            frozenset(['🍌', '♟️', '💩']): full_items.get('🎩'),
            frozenset(['🐟', '🐠', '🐡']): full_items.get('🍣'),
            frozenset(['🐟', '🪼', '🐡']): full_items.get('🍣'),
            frozenset(['🐠', '🪼', '🐡']): full_items.get('🍣'),
            frozenset(['🐠', '🪼', '🐟']): full_items.get('🍣'),
            frozenset(['🐟', '🐡']): full_items.get('🍣'),
            frozenset(['🪼', '🐡']): full_items.get('🍣'),
            frozenset(['🪼', '🐟']): full_items.get('🍣'),
            frozenset(['🪼', '🐠']): full_items.get('🍣'),
            frozenset(['🐡', '🐠']): full_items.get('🍣'),
            frozenset(['🐟', '🐠']): full_items.get('🍣'),
            frozenset(['🪚', '🚪', '🚪']): full_items.get('⛵')

        }

ui_localization = {
    "shop": {
        "Buy_Button": {
            "LANG_RU": "Купить",
            "LANG_EN": "Buy"
        },
        "Back_Button": {
            "LANG_RU": "Назад",
            "LANG_EN": "Back"
        },
        "Shop_Name": {
            "LANG_RU": "Магазин",
            "LANG_EN": "Shop"
        },
        "Description_Label": {
            "LANG_RU": "Описание",
            "LANG_EN": "Description"
        },
        "Money_Warn": {
            "LANG_RU": "У вас не хватает денег!",
            "LANG_EN": "Not enough money!"
        },
        "Buy_Interaction": {
            "LANG_RU": "Вы купили",
            "LANG_EN": "You bought"
        }
    },
    "profile": {
        "Profile_Title": {
            "LANG_RU": "Профиль Игрока",
            "LANG_EN": "The profile of Player"
        },
        "Profile_Pocket": {
            "LANG_RU": "Карман Игрока",
            "LANG_EN": "The pocket of Player"
        },
        "Profile_Currency": {
            "LANG_RU": "Монетки",
            "LANG_EN": "Coins"
        },
        "Profile_Page": {
            "LANG_RU": "страница",
            "LANG_EN": "page"
        },
        "Profile_Button_Previous": {
            "LANG_RU": "Предыдущая страница",
            "LANG_EN": "Previous page"
        },
        "Profile_Button_Next": {
            "LANG_RU": "Следующая страница",
            "LANG_EN": "Next page"
        }
    },
    "info": {
        "Info_No_Inventory": {
            "LANG_RU": "xnj ты информацию ищешь в космосе (пантигон привет)",
            "LANG_EN": "wut you are searching in space (pantigon privet)"
        },
        "Info_Several_Items1": {
            "LANG_RU": "у тебя несколько",
            "LANG_EN": "you have several"
        },
        "Info_Several_Items2": {
            "LANG_RU": "выбери конкретный предмет, чтобы посмотреть информацию о нём",
            "LANG_EN": "choose the specific item, to view some info about it"
        },
        "Info_Several_Items3": {
            "LANG_RU": "(скопируй тег вместе с эмодзи или значение после двоеточий)",
            "LANG_EN": "(copy the tag with emoji OR the value after column)"
        },
        "Info_Item_Obtained": {
            "LANG_RU": "предмет получен",
            "LANG_EN": "item obtained at"
        },
        "Info_Moon_Blessing": {
            "LANG_RU": "Благословление луны",
            "LANG_EN": "Moon's blessing"
        },
        "Info_Rarity": {
            "LANG_RU": "Редкость",
            "LANG_EN": "Rarity"
        },
        "AFK_Warn": {
            "LANG_RU": "ты чет призадумался, попробуй лучше снова",
            "LANG_EN": "you spaced out for a bit, just try again"
        },
        "WRONG_ITEM_Warn": {
            "LANG_RU": "хрень, такого предмета нету",
            "LANG_EN": "nahhh, idk about this item"
        }
    },
    "sell": {
        "Sell_No_Inventory": {
            "LANG_RU": "тебе нечего продать на файерградском рынке",
            "LANG_EN": "you have nothing to sell on firegrad's market"
        },
        "Sell_Several_Item1": {
            "LANG_RU": "ничего себе, у тебя несколько",
            "LANG_EN": "nowaying, you have several"
        },
        "Sell_Several_Item2": {
            "LANG_RU": "выбери чё продать из этого (укажи индекс)",
            "LANG_EN": "choose wat do you want to sell (specify the index)"
        },
        "Sell_Several_Item3": {
            "LANG_RU": 'или напиши "всё" если хочешь продать всё сразу',
            "LANG_EN": 'or write "all" if you want to sell these all'
        },
        "Sell_Start": {
            "LANG_RU": "окей, ща продадим",
            "LANG_EN": "okay, lets sell"
        },
        "Sell_Phrase1": {
            "LANG_RU": "на файерградском рынке купили",
            "LANG_EN": "on firegrad's market was bought"
        },
        "Sell_Phrase2": {
            "LANG_RU": "за",
            "LANG_EN": "for"
        },
        "Sell_Error": {
            "LANG_RU": "запор чето не получилось, ошибка",
            "LANG_EN": "uhh what te heck i got an error"
        }
    },
    "values": {
        "coins": {
            "LANG_RU": "монетки",
            "LANG_EN": "coins"
        },
        "coin": {
            "LANG_RU": "монет",
            "LANG_EN": "coins"
        },
        "cm": {
            "LANG_RU": "см",
            "LANG_EN": "cm"
        }
    },
    "craft": {
        "craft_success": {
            "LANG_RU": "ура, вы скрафтили",
            "LANG_EN": "hooray, you crafted"
        },
        "craft_fail1": {
            "LANG_RU": "ты намудрил с рецептом, и скрафтил",
            "LANG_EN": "you failed and crafted"
        },
        "craft_insufficient_items": {
            "LANG_RU": "ну у тебя каких-то вещей нету в инвентаре",
            "LANG_EN": "well you dont have enough items"
        },
        "craft_fail2": {
            "LANG_RU": "у вас не получилось скрафтить предмет.",
            "LANG_EN": "you failed to craft an item for some reason."
        },
        "craft_possible_usage": {
            "LANG_RU": "возможно, этот предмет используется в крафте",
            "LANG_EN": "maybe THIS item is used in possible craft"
        },
        "craft_no_inventory": {
            "LANG_RU": "ты че как бомжик аид, беги собирать вещи",
            "LANG_EN": "nah bro you dont even have any items what do you think you can craft??"
        }
    },
    "peel": {
        "peel_no_timeout_role": {
            "LANG_RU": "увы даже такой роли нету... пусть админ напишет `/settings` и настроит TIMEOUT_ROLE_ID",
            "LANG_EN": "um there is no such role... go tell admin to write `/settings` and manage the TIMEOUT_ROLE_ID"
        },
        "peel_user_not_in_cage": {
            "LANG_RU": "ты норм, иди отдыхай",
            "LANG_EN": "you ok go chill"
        },
        "peel_quantity_left": {
            "LANG_RU": "вы почистили 🍌, осталось",
            "LANG_EN": "you peeled a 🍌, you still need to peel"
        },
        "peel_escape1": {
            "LANG_RU": "ёмаё",
            "LANG_EN": "no waying"
        },
        "peel_escape2": {
            "LANG_RU": "выпустили из обезяника",
            "LANG_EN": "escapes from the cage"
        },
        "peel_double_cage": {
            "LANG_RU": "да нельзя щас",
            "LANG_EN": "you cant use this command again on the same person bro is trying to peel thousands of bananas and you want to cage him again bro fr? :skull:"
        },

    },
    "cage": {
        "cage_no_timeout_role": {
            "LANG_RU": "какой же всё таки пипец что бот не настроен... админы напишите `/settings` и добавьте TIMEOUT_ROLE_ID (айди роли, которая даётся пользователям для таймаута)",
            "LANG_EN": "bro the bot is not configured... admins pls write `/settings` and add TIMEOUT_ROLE_ID (the id of a role that is given to users for the timeout to start)"
        },
        "cage_long_reason": {
            "LANG_RU": "что биографию свою пишешь чтоли",
            "LANG_EN": "are you writing autobiography or what"
        },
        "cage_bananas_limit": {
            "LANG_RU": "бананы ограничиваются от 0 до 99999",
            "LANG_EN": "bananas are limited from 0 to 99999"
        },
        "cage_already_in": {
            "LANG_RU": "уже там",
            "LANG_EN": "already in cage"
        },
        "cage_incorrect_time": {
            "LANG_RU": "какашечно вводишь время иди читай хелп про команду",
            "LANG_EN": "incorrect time, dude go check help about this command"
        },
        "cage_no_channel": {
            "LANG_RU": "какой же всё таки пипец что бот не настроен... админы напишите `/settings` и добавьте TIMEOUT_CHANNEL_ID (канал для таймаутов)",
            "LANG_EN": "bro the bot is not configured... admins pls write `/settings` and add TIMEOUT_CHANNEL_ID (the id of a channel for timeout)"
        },
        "cage_start": {
            "LANG_RU": "отправляется в орангутан",
            "LANG_EN": "sent to timeout"
        },
        "cage_no_manage_roles": {
            "LANG_RU": "у бота нету прав на выдачу ролей!!",
            "LANG_EN": "the bot doesn't have the manage roles permission!!"
        },
        "cage_welcome1": {
            "LANG_RU": "добро пожаловать в этот канал",
            "LANG_EN": "welcome to this channel"
        },
        "cage_welcome2": {
            "LANG_RU": "вы очевидно в чём-то провинились раз здесь оказались.",
            "LANG_EN": "you've obviously done something wrong to be here."
        },
        "cage_time": {
            "LANG_RU": "Вы будете находиться здесь до",
            "LANG_EN": "You will be here until"
        },
        "cage_note": {
            "LANG_RU": "здесь осталась записка. вот, кстати, её текст",
            "LANG_EN": "there's a note left here. btw this is what written on it"
        },
        "cage_note_author": {
            "LANG_RU": "автор",
            "LANG_EN": "author"
        },
        "cage_escape_condition1": {
            "LANG_RU": "Чтобы выбраться отсюда, вам необходимо",
            "LANG_EN": "To get out of here, you need to"
        },
        "cage_escape_condition2": {
            "LANG_RU": "почистить",
            "LANG_EN": "peel"
        },
        "cage_escape_condition3": {
            "LANG_RU": "используя !peel",
            "LANG_EN": "by using !peel"
        },
        "cage_channel_deletion": {
            "LANG_RU": "кто удалил канал клетки",
            "LANG_EN": "who deleted the timeout channel"
        },
        "cage_escape1": {
            "LANG_RU": "ёмаё",
            "LANG_EN": "no waying"
        },
        "cage_escape2": {
            "LANG_RU": "выпустили из обезяника",
            "LANG_EN": "escapes from the cage"
        },
    },
    "help": {
        "help_standard_commands": {
            "LANG_RU": "Стандартные команды",
            "LANG_EN": "Regular commands"
        },
        "help_dimabot": {
            "LANG_RU": "димабот",
            "LANG_EN": "dimabot"
        },
        "help_gamenight": {
            "LANG_RU": "Геймнайт",
            "LANG_EN": "Game Night"
        },
        "help_economy": {
            "LANG_RU": "Экономика",
            "LANG_EN": "Economy"
        },
        "help_mod": {
            "LANG_RU": "Администрация",
            "LANG_EN": "Moderation"
        },
        "help_other": {
            "LANG_RU": "Другие",
            "LANG_EN": "Others"
        },
        "help_games": {
            "LANG_RU": "Мини-игры",
            "LANG_EN": "Mini-games"
        },
        "help_params_required": {
            "LANG_RU": "Следующие параметры НЕОБХОДИМЫ",
            "LANG_EN": "The following parameters are REQUIRED"
        },
        "help_params_optional": {
            "LANG_RU": "Следующие параметры ОПЦИОНАЛЬНЫ",
            "LANG_EN": "The following parameters are OPTIONAL"
        },
        "help_usage_example": {
            "LANG_RU": "Пример использования",
            "LANG_EN": "Usage example"
        },
        "help_dimabot_helper": {
            "LANG_RU": "димабот помощник",
            "LANG_EN": "dimabot the helper"
        },
        "help_no_command": {
            "LANG_RU": "увы, такой команды нету",
            "LANG_EN": "unfortunately there is no such command"
        },
    },
    "feedback": {
        "feedback_title1": {
            "LANG_RU": "Фидбек",
            "LANG_EN": "Feedback"
        },
        "feedback_title2": {
            "LANG_RU": "Димабот",
            "LANG_EN": "Dimabot"
        },
        "feedback_answer": {
            "LANG_RU": "Ответ на входящий фидбек",
            "LANG_EN": "Feedback reply"
        },
        "feedback_text": {
            "LANG_RU": "Текст",
            "LANG_EN": "Text"
        },
        "feedback_reply": {
            "LANG_RU": "Ответ",
            "LANG_EN": "Reply"
        },
        "feedback_message_url": {
            "LANG_RU": "Ссылка на сообщение",
            "LANG_EN": "Message link"
        },
        "feedback_reply_msg1": {
            "LANG_RU": "ответил на фидбек",
            "LANG_EN": "replied to feedback"
        },
        "feedback_reply_msg2": {
            "LANG_RU": "от",
            "LANG_EN": "from"
        },
        "feedback_reply_button": {
            "LANG_RU": "ответить",
            "LANG_EN": "reply"
        },
        "feedback_sent": {
            "LANG_RU": 'фидбек отправлен (наверное)',
            "LANG_EN": "feedback has been sent (probably)"
        }
    },
    "gamenight_list": {
        "gamenight_list_possible_games": {
            "LANG_RU": "Список возможных игр Геймнайта",
            "LANG_EN": "Possible Game Night event's games"
        },
        "gamenight_list_json": {
            "LANG_RU": "скачать json для вставки в рулетку",
            "LANG_EN": "download json-file"
        },
        "gamenight_list_empty": {
            "LANG_RU": "Лист пуст.",
            "LANG_EN": "The game list is empty."
        }
    },
    "gamenight_start": {
        "gamenight_start_launch": {
            "LANG_RU": "рулетка инициализирована предлагайте игры",
            "LANG_EN": "Game Night Suggestions Initialized, suggest some games plz"
        },
        "gamenight_start_suggest": {
            "LANG_RU": "предложить игру",
            "LANG_EN": "suggest a game or two"
        },
        "gamenight_start_end": {
            "LANG_RU": "геймнайт уже закончился.",
            "LANG_EN": "Game Night event already has ended."
        },
        "gamenight_start_already": {
            "LANG_RU": "ну геймнайт уже начат у твоего сервера.",
            "LANG_EN": "Game Night event has already started on the server."
        }
    },
    "gamenight_end": {
        "gamenight_end_end": {
            "LANG_RU": "предложка всё! больше нельзя предлагать игры.",
            "LANG_EN": "game suggestion was ended. no more games to be suggested."
        },
        "gamenight_end_not_started_error": {
            "LANG_RU": "ау геймнайта ещё нету.",
            "LANG_EN": "there is no game night event yet."
        }
    },
    "gamenight_gamedelete": {
        "gamenight_gamedelete_game_deletion": {
            "LANG_RU": "Успешно удалён элемент",
            "LANG_EN": "Provided element succesfully deleted."
        },
        "gamenight_gamedelete_no_game": {
            "LANG_RU": "Элемент не найден в вашем списке...",
            "LANG_EN": "Provided element was not found in your suggested games."
        },
        "gamenight_gamedelete_no_user": {
            "LANG_RU": "User не найден в списке...",
            "LANG_EN": "User not found in the entirety of suggested games."
        }
    },
    "GameSubmitSurvey": {
        "title": {
            "LANG_RU": "Предложение игр для Геймнайта",
            "LANG_EN": "Game Night event games suggestion"
        },
        "first_game": {
            "LANG_RU": "Название первой игры",
            "LANG_EN": "First game name"
        },
        "second_game": {
            "LANG_RU": "Название второй игры",
            "LANG_EN": "Second game name"
        },
        "third_game": {
            "LANG_RU": "Название третьей игры",
            "LANG_EN": "Third game name"
        },
        "accept_terms": {
            "LANG_RU": "я СОГЛАСЕН что ПРИДЁТСЯ пойти на геймнайт",
            "LANG_EN": "type 'yes' to confirm"
        },
        "placeholder": {
            "LANG_RU": "да",
            "LANG_EN": "yes"
        },
        "no_settings": {
            "LANG_RU": "какой же всё таки пипец что бот не настроен... админы напишите `/settings` и добавьте BOT_CHANNEL_ID (основной канал где бот будет писать)",
            "LANG_EN": "bro the bot is not configured... admins pls write `/settings` and add BOT_CHANNEL_ID (the id of a channel for BOT to send cool messages)"
        },
        "suggested_games": {
            "LANG_RU": "предложил следующие игры",
            "LANG_EN": "suggested the following games"
        }
    }

}

rarity_distribution = {
    0: {'LANG_RU': "опосредственный", 'LANG_EN': "regular"},
    1: {'LANG_RU': "обычненький", 'LANG_EN': 'commonish'},
    2: {'LANG_RU': "необычненький", 'LANG_EN': 'uncommonish'},
    3: {'LANG_RU': "редкостный", 'LANG_EN': "rareish"},
    4: {'LANG_RU': "сверхредкостный", "LANG_EN": "super rareish"},
    5: {'LANG_RU': "эпическеский", "LANG_EN": "epices"},
    6: {'LANG_RU': "мифический!!!!!", "LANG_EN": "mythic!!!!!"},
    7: {'LANG_RU': "легендарка", "LANG_EN": "legendary"},
    8: {'LANG_RU': "деревянный", "LANG_EN": "woody"},
    9: {'LANG_RU': "уникальный", 'LANG_EN': 'unique'}
}
multiplier_distribution = {
    "0 <= abs(round(100 * math.sin(value * math.pi), 9)) <= 50": "🌑",
    "0 <= math.tan(value) <= 1": "🌒",
    "35 <= 40 * (math.tanh(value) + 1) <= 60": "🌓",
    "1 <= 40 * math.exp(-((value-2.5)**2)/2) <= 60": "🌔",
    "int((math.sqrt(5) + 1) / 2 ** value / math.sqrt(5) + 0.5)": "🌕",
    "0 <= math.degrees(value) <= 180": "🌖",
    "0 <= math.gamma(value % 4 + 1) * 10 <= 10": "🌗",
    "0 <= 40 * (1 + math.erf((value-2)/1.4)) <= 20": "🌘"
}


'''
Секция с картами для рыбалки
Формат: Карта, описание, кол-во рыб, координаты hook, координаты лодки, шанс на сокровище, случайные события;
'''

maps = {
    "спокойный океан": [[["◼️", "◼️", "◼️", "◼️", "◼️", "☀️", "◼️"],
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
                         ["🟨", "🟨", "🟨", "🟨", "🟨", "🟨", "🟨"]],
                        "Кажется, что именно здесь находятся все тайны этого мира",
                        3,
                        [4, 3],
                        [2, 3],
                        "placeholder",
                        "placeholder"],

    "попасити 2029 год": [[["🟥","🌫","🌫️","🌫","🟥","🟥","🟥","🟥","🟥"],
                  ["🟧","🟧","🟧","🟧","🟧","🟧","🌫","🌫️","🟧"],
                  ["🌆","🌇","🌆","🟧","🛶","🟧","🟧","🟧","🌆"],
                  ["🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦"],
                  ["🟦","🟦","🟦","🟦","🪝","🟦","🟦","🟦","🟦"],
                  ["🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦"],
                  ["🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦"],
                  ["🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦"],
                  ["🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦","🟦"],
                  ["🟦","🟫","🟦","🪸","🟦","🟦","🟦","🟦","🟫"],
                  ["🟫","🟫","🟫","🟫","🟦","🟦","⚙️","🟫","🟫"],
                  ["🟫","🟫","🟫","🟫","🟫","🟫","🟫","🟫","🟫"]],
                 "Этот индустриальный город развился до таких масштабов, потому что там не было... сами знаете кого",
                 4,
                 [4, 4],
                 [2, 4],
                 "placeholder",
                 "placeholder"]
}

fish_available = {
    'спокойный океан': [['🐟'] * 4 + ['🐠'] * 3 + ['🐡'] * 3 + ['🪼'] * 2 + ['👢'] * 4 + ['🫖'] * 1,
                        ['🐟'] * 5 + ['🐠'] * 3 + ['🐡'] + ['🪼'] + ['👢'] + ['🦐'] * 2 + ['🐙'] + ['🦈'] + ['🐚'] * 2 + ['🫖']],
    'попасити 2029 год': [['🚪'] * 30 + ['🔩'] * 20 + ['📟'] + ['🖲️'] + ['💩'] * 5 + ['👢'] * 5 + ['🫖'],
                          ['🚪'] * 20 + ['🔩'] * 15 + ['📟'] * 3 + ['🖲️'] * 2 + ['💩'] * 1 + ['👢'] * 1, ['🫖']]
}

fish_book = {
                        '🐟': ["вы поймали карася размером {} сантиметров", lambda: 1, "fish"],
                        '🐠': ['вы поймали брата карася размером {} сантиметров', lambda: 1, "fish"],
                        '🐡': ['вы поймали рыбу агу ага размером {} сантиметров', lambda: 1, "fish"],
                        '🪼': ['вы поймали медузу крутую размером {} сантиметров', lambda: 1, "fish"],
                        '🦐': ['вы поймали креветочку размером {} сантиметров', lambda: 1, "fish"],
                        '🦈': ['Трепещи, rer_5111, я поймать АКУЛУ размером {} сантиметров!', lambda: 1, "fish"],
                        '👢': ['вы поймали грязный ботинок из австралии.', lambda: round((random.random() + 1), 9), "item"],
                        '🐚': ['вы поймали плавающую ракушку.', lambda: round((random.random() + 1.256), 5), "item"],
                        '🚪': ['вы поймали Д.В.Е.Р.Ь.', lambda: round((random.random() + 1.38), 9), "item"],
                        '🔩': ["вы поймали болт фром тхандер (на самом деле металлолом...)", lambda: round((random.random() + 0.23), 9),
                              "item"],
                        '📟': ["вы поймали что это нахер", lambda: round((random.random() + 2.4), 9), "item"],
                        '🖲️': ["вы поймали жми на кнопку, кронк", lambda: round((random.random() + 2.14), 9), "item"],
                        '💩': ["фу чё это так воняет, убери этот навоз", lambda: round((random.random() + 1), 9), "item"],
                        '🫖': ["вы поймали... чайник... с функцией... какой-то", lambda: round((random.random() + 0), 9), "quest"]
                    }

"""
НОВЕЛЛЬНАЯ-СЕКЦИЯ
"""

def speech_bubble(text: str, npc: str):
    width = len(text) + 2
    return f"```\n┌{'─' * width}┐\n│ {text} │\n└{'─' * width}┘\n{' ' * (width // 2)}▼\n```{'⠀' * ((width // 2)-1)}{npc}"

rpg_quest_items = {
    '🫖': {
        "item_name": {'LANG_RU': "подозрительный чайник", 'LANG_EN': "suspicious teapot"},
        "multiplier_price": lambda: round((random.random() + 1.7), 9),
        "description": {'LANG_RU': "Этот подозрительный чайник без функции жопа наверняка будет необходим когда-то.",
                        "LANG_EN": "placeholder"},
        "usage": "id28use",
        "shop_price": "0"
    },
}

npc = {
    "🦸": {"npc_name": {'LANG_RU': "антошка, великий сын фермера"}}
}

locations = {
    1: {
        "name":
            {"LANG_RU": "спокойный океан",
            "LANG_EN": "peaceful ocean"},
        "place_image": "placeholder1.png",
        "description":
            {"LANG_RU": "ОЧЕНЬ привлекательное место для отдыха, но здесь почти никто не обитает.",
            "LANG_EN": "VERY attractive place for chill & stuff, however almost no one lives there."},
        "npc": ["🦸"],
        "options": {
            "placeholder": {
                "LANG_RU": "Выберите ваше действие...",
                "LANG_EN": "Choose your action..."
            },
            "talk": {
                "LANG_RU": "поговорить",
                "LANG_EN": "talk"
            },
            "talk_with": {
                "LANG_RU": "Поговорить с...?",
                "LANG_EN": "To talk with...?"
            }
        }
    }
}

rpg_lore_quests = {
    "🦸": {
        1: {
            None: {
                "new_quest_id": 1,
                "name": {
                    "LANG_RU": "поймай-ка рыбку",
                    "LANG_EN": "catch da fish"

                },
                "requirements": 1,
                "lines": {
                    "LANG_RU": [
                        "привет", "я антошка, великий сын фермера!", "у меня для тебя задание", "налови любые 10 рыб пж"
                    ],
                    "LANG_EN": [
                        "hello", "im antoshka, the greatest son of a farmer", "i have a quest ready for you", "catch any 10 fish pls"
                    ]
                },
                "end_line": {
                    "LANG_RU": "ну короче давай жду",
                    "LANG_EN": "ok go im waiting"
                }
            },
            1: {
                "new_quest_id": 2,
                "name": {
                    "LANG_RU": "напряг мозжечка",
                    "LANG_EN": "use your Cerebellum™"
                },
                "requirements": '''sum(1 for key in inventory_ref.child(str(user_id)).get().keys() if fish_book.get(re.sub(r'[0-9]', '', key))[2] == "fish") >= 10''',
                "meet_no_requirements": {
                    "LANG_RU": [
                        "ну ты ещё не поймал", "возвращайся позже", "я пока буду смотреть на песок"
                    ],
                    "LANG_EN": [
                        "your not done with fishing yet", "come back when you done", "im going to look at the sand"
                    ]
                },
                "lines": {
                    "LANG_RU": [
                        "ура ты умеешь рыбачить", "награды не будет у меня у самого денег нету", "ну короче новый квест тебе", "говорят в водах здешних...", "...есть чайниичек", "поймай его и принеси"
                    ],
                    "LANG_EN": [
                        "yay youcan fish", "no reward tho cuz im broke too", "so new quest for ya", "they say there is a thing in nearby waves...", "...they call it kettle", "catch it and give it to me"
                    ]
                },
                "end_line": {
                    "LANG_RU": "он вроде как редкий, так что, увы, придется гриндить",
                    "LANG_EN": "this item is kinda rare so you have to grind *unfortunately*"
                }
            },
            2: {
                "new_quest_id": 3,
                "name": {
                    "LANG_RU": "филлерный эпизод",
                    "LANG_EN": "filler episode"
                },
                "requirements": '''1 for key in inventory_ref.child(str(user_id)).get().keys() if rpg_quest_items.get(re.sub(r'[0-9]', '', key))[3] == "id28use") >= 1''',
                "meet_no_requirements": {
                    "LANG_RU": [
                        "спасибо за помощь"
                    ],
                    "LANG_EN": [
                        "thanks for the help"
                    ]
                },
                "lines": {
                    "LANG_RU": ["ладно", "я передумал", "можешь оставить это себе", "это ценный артефакт", "протри его (!use 🫖)"],
                    "LANG_EN": ["ok", "i changed my mind", "you can have it", "its a very valuable artifact", "rub it (!use 🫖)"]
                },
                "end_line": {
                    "LANG_RU": "спасибо за помощь, правда",
                    "LANG_EN": "thanks for the help fr"
                }
            }
       }
    }
}

