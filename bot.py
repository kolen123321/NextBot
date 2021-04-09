from discord.ext import commands
import json
from models import *
from discord import Embed
import datetime, time
import random
from discord.utils import get
from validators import *
from utils import *

config = json.loads(open("config.json", "r").read())

theme = {
    'success': 0x29af1d,
    'error': 0xe40707,
    'info': 0x0784e4
}

bot = commands.Bot(command_prefix="!")

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
    

bot.run(config['bot']['token'])