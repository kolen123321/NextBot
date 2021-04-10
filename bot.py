from discord.ext import commands
import json
from models import *
from discord import Embed
import datetime, time
import random
from discord.utils import get
from validators import *
from utils import *
import discord

config = json.loads(open("config.json", "r").read())

theme = {
    'success': 0x29af1d,
    'error': 0xe40707,
    'info': 0x0784e4
}
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

bot.remove_command('help')


def incline_coin(number):
    last_num = round(float(number)) % 10
    if last_num == 1:
        return "NextCoin"
    elif last_num == 2 or last_num == 3 or last_num == 4:
        return "NextCoin-а"
    elif last_num == 5 or last_num == 6 or last_num == 7 or last_num == 8 or last_num == 9 or last_num == 0:
        return "NextCoin-ов"

def incline(number, word):
    last_num = round(float(number)) % 10
    if last_num == 1:
        return word
    elif last_num == 2 or last_num == 3 or last_num == 4:
        return f"{word}-а"
    elif last_num == 5 or last_num == 6 or last_num == 7 or last_num == 8 or last_num == 9 or last_num == 0:
        return f"{word}-ов"
    

def error(title="Ошибка", message="Ничего"):
    embed=Embed(color=theme['error'])
    embed.add_field(name=title, value=message, inline=False)
    return embed

def info(title="Информация", message="Ничего"):
    embed=Embed(color=theme['info'])
    embed.add_field(name=title, value=message, inline=False)
    return embed

def success(title="Успех", message="Ничего"):
    embed=Embed(color=theme['success'])
    embed.add_field(name=title, value=message, inline=False)
    return embed

def get_item(owner, item_name, create=True):
    check_connection()
    item = Item.select().where(Item.owner == owner, Item.name == item_name)
    if not item.exists():
        if create:
            item = Item()
            item.owner = owner
            item.name = item_name
            item.save()
        else:
            item = None
    else:
        item = item[0]
    close_connection()
    return item


async def create_or_get_user(ctx):
    check_connection()
    user = User.select().where(User.userid == ctx.author.id)
    if not user.exists():
        user = User()
        user.userid = ctx.author.id
        user.save()
    user = User.get(User.userid == ctx.author.id)
    close_connection()
    return user

async def nextbank(ctx):
    embed=Embed(color=theme['success'])
    embed.add_field(name="NextBank", value="Сервис", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="account", aliases=['a', 'acc'])
async def account(ctx):
    check_connection()
    if ctx.channel.id == config['channels']['nextbank']['client']:
        user = await create_or_get_user(ctx)
        embed=Embed(title=f"Счет {ctx.author}", color=theme['info'])
        embed.add_field(name="Баланс", value=f"{user.balance} {incline_coin(user.balance)}", inline=False)
        await ctx.send(embed=embed)
    close_connection()

@bot.event
async def on_raw_reaction_add(payload):
    if payload.guild_id == None and payload.emoji.name == "❌":
        print(bot.private_channels)

@bot.command(name="verify", aliases=['v'])
async def verify(ctx, *args):
    check_connection()
    if ctx.channel.id == config['channels']['nextbank']['client']:
        if len(args) == 0:
            user = await create_or_get_user(ctx)
            verify = Code()
            verify.owner = user
            verify.code = random.randint(1000, 9999)
            verify.save()
            embed=Embed(color=theme['info'])
            embed.add_field(name="Верефикация", value=f"Ваш верефикационый код: {verify.code}\nНикому не говорите данный код", inline=False)
            message = await ctx.author.send(embed=embed)
            embed=Embed(color=theme['info'])
            embed.add_field(name="Верефикация", value=f"Я отправил код вам в личные сообщения", inline=False)
            await ctx.send(embed=embed)
    elif ctx.guild.get_role(config['roles']['banker']) in ctx.author.roles and ctx.channel.id == config['channels']['nextbank']['banker']:
        if len(args) == 1:
            user = await create_or_get_user(ctx)
            verify = Code.select().where(Code.code == args[0])
            if verify.exists():
                verify = Code.get(Code.code == args[0])
            else:
                await ctx.send(embed=error(message="Код не найден"))
                return False
            touser = verify_code(verify)
            embedColor = theme['info']
            if touser:
                title = "Верефикация"
                message = f"Пользовотель: <@!{touser.userid}>"
            else:
                embedColor = theme['error']
                title = "Ошибка"
                message = "Код не найден или его срок действия истёк"
            embed=Embed(color=embedColor)
            embed.add_field(name=title, value=message, inline=False)
            await ctx.send(embed=embed)
    close_connection()

@bot.command(name="inventory", aliases=['inv', 'i'])
async def inventory(ctx):
    check_connection()
    if ctx.channel.id == config['channels']['nextbank']['client']:
        user = await create_or_get_user(ctx)
        items = Item.select().where(Item.owner == user.id)
        items_in_str = ""
        num = 0
        for item in items:
            num += 1
            items_in_str += f"{num}. {item.name} x{item.amount}\n"
        if len(items) < 1:
            items_in_str = "Пусто..."
        embed=Embed(title=f"Предметы клиента {ctx.author}", color=theme['info'], description=items_in_str)
        await ctx.send(embed=embed)

@bot.command(name="give", aliases=['g'])
async def give(ctx, *args):
    check_connection()
    if ctx.channel.id == config['channels']['nextbank']['client']:
        embedColor = theme['info']
        if len(args) == 3:
            user = await create_or_get_user(ctx)
            touserid = PingValidator(args[0]).data
            if not touserid:
                await ctx.send(embed=error(message="Поле <Клиент> введено неправильно"))
                return False
            touser = User.select().where(User.userid == touserid)
            if not touser.exists():
                await ctx.send(embed=error(message="Клиент не имеет счета"))
                return False
            touser = touser.first()
            amount = AmountValidator(args[2]).data
            if not amount:
                await ctx.send(embed=error(message="Поле <Кол-во> введено неправильно"))
                return False
            item = get_item(user.id, args[1], create=False)
            if not item:
                await ctx.send(embed=error(message="У вас нет данного предмета"))
                return False
            toitem = get_item(touser.id, args[1])
            toitem.amount += amount
            item.amount -= amount
            item.save()
            toitem.save()
            if item.amount <= 0:
                item.delete_instance()
            if toitem.amount <= 0:
                toitem.delete_instance()
            embedColor = theme['success']
            title = "Успех"
            message = f"Вы успешно передали {item.name} x{amount} клиенту <@!{touser.userid}>"
        else:
            embedColor = theme['info']
            title = "Команда"
            message = "!give <Клиент> <Предмет> <Кол-во>\n\nПример: !give <@!708326089440886836> Блок_земли 64"
        print(ctx.author.id)
        embed=Embed(color=embedColor)
        embed.add_field(name=title, value=message, inline=False)
        await ctx.send(embed=embed)

@bot.command(name="help")
async def help(ctx):
    check_connection()
    if ctx.channel.id == 827989670541393920:
        embed=Embed(title=f"NextBank - помощь", color=theme['info'])
        embed.add_field(name="!help", value="Выводит данный список", inline=False)
        embed.add_field(name="!account", value="Выводит ифнормацию о вашем счете", inline=False)
        embed.add_field(name="!verify", value="Команда для получения верефикационого кода", inline=False)
        embed.add_field(name="!pay <Клиент> <Кол-во NextCoin-ов>", value="Команда для получения верефикационого кода", inline=False)
        embed.add_field(name="!give <Клиент> <Название предмета> <Кол-во предметов>", value="Команда для получения верефикационого кода", inline=False)
        embed.add_field(name="!inventory или !inv", value="Выводит информацию о ваших вещах в банке", inline=False)
    elif ctx.channel.id == 828200330969481248:
        embed=Embed(title=f"NextBank - помощь", color=theme['info'])
        embed.add_field(name="!help", value="Выводит данный список", inline=False)
        embed.add_field(name="!manage <Действие> <Клиент> <Кол-во NextCoin-ов>", value="Команда для банкиров", inline=False)
        embed.add_field(name="!verify <Код>", value="Команда для верефикации клиента", inline=False)
        embed.add_field(name="<Действия>", value="add - добавление счета, remove - уменьшение счета", inline=False)
        embed.add_field(name="<Клиент>", value="Пинг клиента", inline=False)
        embed.add_field(name="<Кол-во NextCoin-ов>", value="Кол-во NextCoin-ов", inline=False)
    elif ctx.channel.id == config['channels']['nextdelivery']['client']:
        embed=Embed(title=f"NextDelivery - помощь", color=theme['info'])
        embed.add_field(name="!help", value="Выводит данный список", inline=False)
        embed.add_field(name="!order <Склад откуда> <Склад куда>", value="Команда для создания заказа", inline=False)
        embed.add_field(name="!start <Номер заказа>", value="Команда для запуска заказа после старта с вас пишут 1 NextCoin", inline=False)
        embed.add_field(name="!orders", value="Выводит список ваших заказов", inline=False)
        embed.add_field(name="!storages", value="Выводит список складов NextDelivery")
    elif ctx.channel.id == config['channels']['nextdelivery']['notice']:
        embed=Embed(title=f"NextDelivery - помощь", color=theme['info'])
        embed.add_field(name="!help", value="Выводит данный список", inline=False)
        embed.add_field(name="!accept <Номер заказа>", value="Команда для принятия заказа", inline=False)
        embed.add_field(name="!delivery <Номер заказа>", value="Команда для здачи заказа", inline=False)
        embed.add_field(name="!orders", value="Выводит список ваших принятых заказов", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="pay")
async def pay(ctx, *args):
    check_connection()
    if ctx.channel.id == config['channels']['nextbank']['client']:
        embedColor = theme['success']
        if len(args) == 2:
            touser, amount = args
            
            user = await create_or_get_user(ctx)
            touserid = PingValidator(touser).data
            amount = FloatAmountValidator(amount).data
            if not amount:
                await ctx.send(embed=error(message="Значение <Кол-во NextCoin-ов> введено неправильно"))
                return False
            if not touserid:
                await ctx.send(embed=error(message="Значение <Клиент> введено неправильно"))
                return False
            touser = User.select().where(User.userid == touserid)
            if not touser.exists():
                await ctx.send(embed=error(message="Клиент не найден"))
                return False
            touser = User.select().where(User.userid == touserid).first()
            user.balance -= amount
            touser.balance += amount
            touser.save()
            user.save()
            title = "Успех"
            message = f"Вы успешно перевели {amount} {incline_coin(amount)} клиенту <@!{touser.userid}>"
        else:
            embedColor = theme['info']
            title = "Команда"
            message = f"!pay <Клиент> <Кол-во NextCoin-ов>\n\nПример: !pay <@!708326089440886836> 10"
        embed=Embed(color=embedColor)
        embed.add_field(name=title, value=message, inline=False)
        await ctx.send(embed=embed)
    close_connection()

@bot.command(name='cours', aliases=['c'])
async def cours(ctx):
    if ctx.channel.id == config['channels']['nextbank']['client']:
        check_connection()
        cours = Settings.get(Settings.name == "cours")
        cours = float(cours.data)
        embed=Embed(color=theme['info'])
        embed.add_field(name='Курс NextCoin-а', value=f'1 NextCoin = {cours} {incline(cours, "алмаз")}', inline=False)
        await ctx.send(embed=embed)
        close_connection()

@bot.command(name="manage")
async def account(ctx, *args):
    if ctx.guild.get_role(config['roles']['banker']) in ctx.author.roles and ctx.channel.id == config['channels']['nextbank']['banker']:
        check_connection()
        user = await create_or_get_user(ctx)
        embedColor = theme['success']
        if len(args) > 0: action = args[0]
        if len(args) > 1: user = args[1]
        if len(args) > 2: diamonds = args[2]
        if len(args) > 2:
            if action == "add":
                userid = user.replace("<@!", "").replace(">", "")
                touser = User.select().where(User.userid == userid)
                diamonds = float(diamonds)
                amount = diamonds
                if not touser.exists():
                    await ctx.send(embed=error(message="Клиент не найден"))
                    return False
                touser = touser.first()
                touser.balance += float(amount)
                touser.save()
                title = "Успех"
                message = f"Вы успешно добавили {amount} {incline_coin(amount)} клиенту <@!{touser.userid}>"
            elif action == "remove":
                userid = user.replace("<@!", "").replace(">", "")
                touser = User.select().where(User.userid == userid)
                amount = diamonds
                amount_pr = float(amount) + (float(amount) / 100 * 5)
                if not touser.exists():
                    await ctx.send(embed=error(message="Клиент не найден"))
                    return False
                touser = touser.first()
                if touser.balance - amount_pr > 0:
                    amount = amount_pr
                touser.balance -= float(amount)
                touser.save()
                title = "Успех"
                message = f"Вы успешно отняли {amount} {incline_coin(amount)} у клиента <@!{touser.userid}>"
            embed = Embed(color=embedColor)
            embed.add_field(name=title, value=message)
            await ctx.send(embed=embed)
        close_connection()

@bot.command(name="items")
async def items(ctx, *args):
    user = await create_or_get_user(ctx)
    if ctx.guild.get_role(config['roles']['banker']) in ctx.author.roles and ctx.channel.id == config['channels']['nextbank']['banker']:
        check_connection()
        embedColor = theme['success']
        if len(args) > 0: action = args[0]
        if len(args) > 1: user = args[1]
        if len(args) > 2: itemName = args[2]
        if len(args) > 3: amount = AmountValidator(args[3]).data
        if 3 > len(args) > 1:
            embedColor = theme['info']
            if action == "get":
                userid = user.replace("<@!", "").replace(">", "")
                touser = User.select().where(User.userid == userid).first()
                items = Item.select().where(Item.owner == touser)
                items_in_str = f"Клиент <@!{touser.userid}>"
                i = 0
                for item in items:
                    days = round((datetime.datetime.now() - item.created).total_seconds() / 60 / 60 / 24, 1)
                    i += 1
                    items_in_str += f"\n{i}. {item.name} x{item.amount}, дней храниться: {days}"
                if len(list(items)) < 1:
                    items_in_str += "\nПусто..."
                message = f"{items_in_str}"
                title = "Предметы"
                embed = Embed(color=embedColor)
                embed.add_field(name=title, value=message)
                await ctx.send(embed=embed)
        if len(args) > 3:
            if action == "add":
                touserid = user.replace("<@!", "").replace(">", "")
                touser = User.select().where(User.userid == touserid).first()
                item = get_item(touser, itemName)
                item.amount += amount
                item.save()
                title = "Успех"
                message = f"Вы успешно добавили предмет \"{item.name}\" x{amount} клиенту <@!{touser.userid}>"
            elif action == "remove":
                touserid = user.replace("<@!", "").replace(">", "")
                touser = User.select().where(User.userid == touserid).first()
                item = get_item(touser, itemName)
                if item.amount >= 0 and item.amount - int(amount) >= 0:
                    item.amount -= int(amount)
                else:
                    message = f"Вы не можете отнять больше предметов чем есть у клиента"
                    embedColor = theme['error']
                    return False
                if item.amount <= 0:
                    item.delete_instance()
                item.save()
                title = "Успех"
                message = f"Вы успешно отняли предмет \"{item.name}\" x{amount} клиенту <@!{touser.userid}>"
            embed = Embed(color=embedColor)
            embed.add_field(name=title, value=message)
            await ctx.send(embed=embed)
        close_connection()

@bot.command(name="order")
async def order(ctx, *args):
    if ctx.channel.id == config['channels']['nextdelivery']['client']:
        check_connection()
        user = await create_or_get_user(ctx)
        from_storage, to_storage = args
        from_storage = Storage.get(Storage.id == int(from_storage))
        to_storage = Storage.get(Storage.id == int(to_storage))
        
        to_cell = Cell.select().where((Cell.order == None) & (Cell.storage == to_storage)).first()
        from_cell = Cell.select().where((Cell.order == None) & (Cell.storage == from_storage)).first()
        if not to_cell:
            await ctx.send(embed=error(message="Склад <Куда> переполнен, пожалуйста попробуйте позже"))
            return False
        if not from_cell:
            await ctx.send(embed=error(message="Склад <Откуда> переполнен, пожалуйста попробуйте позже"))
            return False
        order = Order()
        order.owner = user
        order.to_storage = to_storage
        order.from_storage = from_storage
        order.save()
        to_cell.order = order
        from_cell.order = order
        to_cell.save()
        from_cell.save()
        await ctx.send(embed=success(message=f"Вы успешно создали заказ, ячейка <Откуда>: {from_cell.number} ячейка <Куда>: {to_cell.number}\nПосле того как положите предмет(-ы) пропишите:\n!start {order.id}"))
        close_connection()

@bot.command(name="storages")
async def storages(ctx):
    if ctx.channel.id == config['channels']['nextdelivery']['client']:
        storages = Storage.select().where(1)
        storages_in_str = ""
        for s in storages:
            storages_in_str += f"№{s.id} описание: {s.description} координаты: {s.coordinates}\n"
        await ctx.send(embed=info(title="Склады NextDelivery", message=f"{storages_in_str}"))


@bot.command(name="orders")
async def orders(ctx, *args):
    if ctx.channel.id == config['channels']['nextdelivery']['client']:
        check_connection()
        user = await create_or_get_user(ctx)
        orders = Order.select().where(Order.owner == user)
        orders_in_str = ""
        for o in orders:
            if o.status == "WAIT":
                status = "Ждет предмет(-ы)"
            elif o.status == "STARTED":
                status = "Ждет курьера"
            elif o.status == "DELIVERY":
                status = "В пути"
            to_cell = Cell.get((Cell.order == o) & (Cell.storage == o.to_storage))
            from_cell = Cell.get((Cell.order == o) & (Cell.storage == o.from_storage))
            orders_in_str += f"№{o.id} статус: {status} ячейка \"Откуда\": {from_cell.number} \"Куда\": {to_cell.number}\n"
        if len(orders_in_str) <= 0:
            orders_in_str = "Пусто..."
        await ctx.send(embed=info(title="Ваши заказы",message=f"{orders_in_str}"))
        close_connection()
    elif ctx.channel.id == config['channels']['nextdelivery']['notice']:
        check_connection()
        user = await create_or_get_user(ctx)
        orders = Order.select().where(Order.courier == user)
        orders_in_str = ""
        for o in orders:
            to_cell = Cell.get((Cell.order == o) & (Cell.storage == o.to_storage))
            from_cell = Cell.get((Cell.order == o) & (Cell.storage == o.from_storage))
            orders_in_str += f"№{o.id} ячейка \"Откуда\": {from_cell.number} \"Куда\": {to_cell.number}\n"
        if len(orders_in_str) <= 0:
            orders_in_str = "Пусто..."
        await ctx.send(embed=info(title="Ваши принятые заказы", message=f"{orders_in_str}"))
        close_connection()

import peewee

@bot.command(name="start")
async def start(ctx, *args):
    if ctx.channel.id == config['channels']['nextdelivery']['client']:
        check_connection()
        user = await create_or_get_user(ctx)
        courier_notice_channel = discord.utils.get(ctx.guild.channels, id=830148887573954640)
        try:
            order = Order.get(int(args[0]))
        except peewee.DoesNotExist:
            await ctx.send(embed=error(message="Заказ не найден"))
            return False
        except ValueError:
            await ctx.send(embed=error(message="Значение <Номер заказа> введено неверно"))
            return False
        if order.status != "WAIT":
            await ctx.send(embed=error(message="Заказ уже создан"))
            return False
        delivery_price = 1
        if user.balance >= delivery_price:
            user.balance -= delivery_price
            user.save()
        else:
            await ctx.send(embed=error(message="У вас недостаточно средств"))
            return False
        order.status = "STARTED"
        order.save()
        to_cell = Cell.get((Cell.order == order) & (Cell.storage == order.to_storage))
        from_cell = Cell.get((Cell.order == order) & (Cell.storage == order.from_storage))
        await ctx.send(embed=success(message="Заказ создан\nС вас списали 1 NextCoin"))
        from_storage = from_cell.storage.id
        to_storage = to_cell.storage.id
        await courier_notice_channel.send(embed=info(title="Новый заказ", message=f"Ячейка <Откуда>: {from_storage} {from_cell.number} ячейка <Куда>: {to_storage} {to_cell.number}\nДля того что-бы принять заказ пропишите:\n!accept {order.id}"))
        close_connection()

@bot.command(name="accept")
async def start(ctx, *args):
    if ctx.channel.id == config['channels']['nextdelivery']['notice']:
        check_connection()
        user = await create_or_get_user(ctx)
        try:
            order = Order.get(int(args[0]))
        except peewee.DoesNotExist:
            await ctx.send(embed=error(message="Заказ не найден"))
            return False
        except ValueError:
            await ctx.send(embed=error(message="Значение <Номер заказа> введено неверно"))
            return False
        if order.courier:
            await ctx.send(embed=error(message="Заказ уже взят"))
            return False
        if order.status == "WAIT":
            await ctx.send(embed=error(message="Заказ еще не достиг нужной стадии"))
            return False
        to_user = order.owner.userid
        to_user = discord.utils.get(ctx.guild.members, id=to_user)
        order.status = "DELIVERY"
        order.courier = user
        order.save()
        await to_user.send(embed=info(title="Уведомление NextDelivery", message=f"Ваш заказ №{order.id} был взят курьером <@!{user.userid}>"))
        await ctx.send(embed=success(message=f"Вы успешно взяли заказ №{order.id}"))
        close_connection()

@bot.command(name="delivery")
async def start(ctx, *args):
    if ctx.channel.id == config['channels']['nextdelivery']['notice']:
        check_connection()
        user = await create_or_get_user(ctx)
        try:
            order = Order.get(int(args[0]))
        except peewee.DoesNotExist:
            await ctx.send(embed=error(message="Заказ не найден"))
            return False
        except ValueError:
            await ctx.send(embed=error(message="Значение <Номер заказа> введено неверно"))
            return False
        if order.courier != user:
            await ctx.send(embed=error(message="Вы не курьер данного заказа"))
            return False
        if order.status == "STARTED":
            await ctx.send(embed=error(message="Заказ еще не достиг нужной стадии"))
            return False
        to_user = order.owner.userid
        to_user = discord.utils.get(ctx.guild.members, id=to_user)
        await to_user.send(embed=info(title="Уведомление NextDelivery", message=f"Ваш заказ №{order.id} был доставлен курьером <@!{user.userid}>"))
        await ctx.send(embed=success(message=f"Вы успешно доставили заказ №{order.id}"))
        to_cell = Cell.get((Cell.order == order) & (Cell.storage == order.to_storage))
        from_cell = Cell.get((Cell.order == order) & (Cell.storage == order.from_storage))
        to_cell.order = None
        from_cell.order = None
        to_cell.save()
        from_cell.save()
        user.balance += 1
        user.save()
        order.delete_instance()
        close_connection()
    

bot.run(config['bot']['token'])