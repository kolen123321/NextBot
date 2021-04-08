from discord.ext import commands
import json
from models import *
from discord import Embed
import datetime, time
import random
from discord.utils import get
from validators import *

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
    

def error(title="Ошибка", message="Ничего"):
    embed=Embed(color=theme['error'])
    embed.add_field(name=title, value=message, inline=False)
    return embed

def get_item(session, owner, item_name, create=True):
    item = session.query(Item).filter(Item.owner == owner, Item.name == item_name)
    if not Utils.exists(item):
        if create:
            item = Item()
            item.owner = owner
            item.name = item_name
            session.add(item)
            session.commit()
        else:
            item = None
    else:
        item = item[0]
    return item


async def create_or_get_user(ctx):
    session = make_session()
    user = session.query(User).filter(User.userid == ctx.author.id)
    if not Utils.exists(user):
        user = User()
        user.userid = ctx.author.id
        session.add(user)
        session.commit()
    user = list(session.query(User).filter(User.userid == ctx.author.id))[0]
    return user

async def nextbank(ctx):
    embed=Embed(color=theme['success'])
    embed.add_field(name="NextBank", value="Сервис", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="account", aliases=['a', 'acc'])
async def account(ctx):
    if ctx.channel.id == 827989670541393920:
        user = await create_or_get_user(ctx)
        embed=Embed(title=f"Счет {ctx.author}", color=theme['info'])
        embed.add_field(name="Баланс", value=f"{user.balance} {incline_coin(user.balance)}", inline=False)
        await ctx.send(embed=embed)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.guild_id == None and payload.emoji.name == "❌":
        print(bot.private_channels)

@bot.command(name="verify", aliases=['v'])
async def verify(ctx, *args):
    session = make_session()
    if ctx.channel.id == 827989670541393920:
        if len(args) == 0:
            user = await create_or_get_user(ctx)
            verify = Code()
            verify.owner = user.id
            verify.code = random.randint(1000, 9999)
            session.add(verify)
            session.commit()
            embed=Embed(color=theme['info'])
            embed.add_field(name="Верефикация", value=f"Ваш верефикационый код: {verify.code}\nНикому не говорите данный код", inline=False)
            message = await ctx.author.send(embed=embed)
            embed=Embed(color=theme['info'])
            embed.add_field(name="Верефикация", value=f"Я отправил код вам в личные сообщения", inline=False)
            await ctx.send(embed=embed)


    elif ctx.guild.get_role(827988395116331048) in ctx.author.roles and ctx.channel.id == 828200330969481248:
        if len(args) == 1:
            user = await create_or_get_user(ctx)
            verify = session.query(Code).filter(Code.code == args[0])
            touser = verify_code(args[0])
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

@bot.command(name="inventory", aliases=['inv', 'i'])
async def inventory(ctx):
    if ctx.channel.id == 827989670541393920:
        session = make_session()
        user = await create_or_get_user(ctx)
        items = list(session.query(Item).filter(Item.owner == user.id))
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
async def inventory(ctx, *args):
    if ctx.channel.id == 827989670541393920:
        embedColor = theme['info']
        if len(args) == 3:
            session = make_session()
            user = await create_or_get_user(ctx)
            touserid = PingValidator(args[0]).data
            if not touserid:
                await ctx.send(embed=error(message="Поле <Клиент> введено неправильно"))
                return False
            touser = session.query(User).filter(User.userid == touserid)
            if not Utils.exists(touser):
                await ctx.send(embed=error(message="Клиент не имеет счета"))
                return False
            touser = touser[0]
            amount = AmountValidator(args[2]).data
            if not amount:
                await ctx.send(embed=error(message="Поле <Кол-во> введено неправильно"))
                return False
            item = get_item(session, user.id, args[1], create=False)
            if not item:
                await ctx.send(embed=error(message="У вас нет данного предмета"))
                return False
            toitem = get_item(session, touser.id, args[1])
            toitem.amount += amount
            item.amount -= amount
            if item.amount <= 0:
                session.delete(item)
            if toitem.amount <= 0:
                session.delete(toitem)
            session.commit()
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
    if ctx.channel.id == 827989670541393920:
        embed=Embed(title=f"NextBank - помощь", color=theme['info'])
        embed.add_field(name="!help", value="Выводит данный список", inline=False)
        embed.add_field(name="!account", value="Выводит ифнормацию о вашем счете", inline=False)
        embed.add_field(name="!verify", value="Команда для получения верефикационого кода", inline=False)
        embed.add_field(name="!pay <Клиент> <Кол-во NextCoin-ов>", value="Команда для получения верефикационого кода", inline=False)
        embed.add_field(name="!give <Клиент> <Название предмета> <Кол-во предметов>", value="Команда для получения верефикационого кода", inline=False)
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
    if ctx.channel.id == 827989670541393920:
        if len(args) == 2:
            touser, amount = args
            session = make_session()
            user = await create_or_get_user(ctx)
            touserid = touser.replace("<@!", "").replace(">", "")
            try:
                amount = float(amount)
            except:
                embed=Embed(color=theme['error'])
                embed.add_field(name="Ошибка", value="Вы в вели неправильно значение \"Сумма\"", inline=False)
                await ctx.send(embed=embed)
                return False
            try:
                touserid = int(touserid)
            except:
                embed=Embed(color=theme['error'])
                embed.add_field(name="Ошибка", value="Вы в вели неправильно значение \"Клиент\"", inline=False)
                await ctx.send(embed=embed)
                return False
            if user.balance < amount:
                embed=Embed(color=theme['error'])
                embed.add_field(name="Ошибка", value="У вас недостаточно средств", inline=False)
                await ctx.send(embed=embed)
                return False
            touser = session.query(User).filter(User.userid == touserid)
            if not Utils.exists(touser):
                embed=Embed(color=theme['error'])
                embed.add_field(name="Ошибка", value="Клиент не найден", inline=False)
                await ctx.send(embed=embed)
                return False
            touser = list(session.query(User).filter(User.userid == touserid))[0]
            touser.balance += amount
            user.balance -= amount
            session.commit()
            embed=Embed(color=theme['success'])
            embed.add_field(name="Успех", value=f"Вы успешно перевели {amount} {incline_coin(amount)} клиенту <@!{touser.userid}>", inline=False)
            await ctx.send(embed=embed)
        else:
            embed=Embed(color=theme['info'])
            embed.add_field(name="Команда", value=f"!pay <Клиент> <Кол-во NextCoin-ов>\n\nПример: !pay <@!708326089440886836> 10", inline=False)
            await ctx.send(embed=embed)


@bot.command(name="manage")
async def account(ctx, *args):
    user = await create_or_get_user(ctx)
    session = make_session()
    if ctx.guild.get_role(827988395116331048) in ctx.author.roles and ctx.channel.id == 828200330969481248:
        if len(args) > 0: action = args[0]
        if len(args) > 1: user = args[1]
        if len(args) > 2: amount = args[2]
        if len(args) > 2:
            if action == "add":
                userid = user.replace("<@!", "").replace(">", "")
                touser = session.query(User).filter(User.userid == userid)[0]
                touser.balance += float(amount)
                session.commit()
                embed = Embed(color=theme['success'])
                embed.add_field(name=f"Успех", value=f"Вы успешно добавили {amount} {incline_coin(amount)}  клиенту <@!{touser.userid}>")
                await ctx.send(embed=embed)
            elif action == "remove":
                userid = user.replace("<@!", "").replace(">", "")
                touser = session.query(User).filter(User.userid == userid)[0]
                amount_pr = float(amount) + (float(amount) / 100 * 5)
                if touser.balance - amount_pr > 0:
                    amount = amount_pr
                touser.balance -= float(amount)
                session.commit()
                embed = Embed(color=theme['success'])
                embed.add_field(name=f"Успех", value=f"Вы успешно сняли {amount} {incline_coin(amount)}  клиенту <@!{touser.userid}>")
                await ctx.send(embed=embed)

@bot.command(name="items")
async def items(ctx, *args):
    user = await create_or_get_user(ctx)
    session = make_session()
    if ctx.guild.get_role(827988395116331048) in ctx.author.roles and ctx.channel.id == 828200330969481248:
        embedColor = theme['success']
        if len(args) > 0: action = args[0]
        if len(args) > 1: user = args[1]
        if len(args) > 2: itemName = args[2]
        if len(args) > 3: amount = args[3]
        if len(args) > 1:
            embedColor = theme['info']
            if action == "get":
                userid = user.replace("<@!", "").replace(">", "")
                touser = session.query(User).filter(User.userid == userid)[0]
                items = session.query(Item).filter(Item.owner == touser.id)
                embed = Embed(color=embedColor)
                items_in_str = f"Клиент <@!{touser.userid}>"
                i = 0
                for item in items:
                    days = round((datetime.datetime.now() - item.created).total_seconds() / 60 / 60 / 24, 1)
                    i += 1
                    items_in_str += f"\n{i}. {item.name} x{item.amount}, дней храниться: {days}"
                if len(list(items)) < 1:
                    items_in_str = "Пусто..."
                embed.add_field(name=f"Предметы", value=items_in_str)
                await ctx.send(embed=embed)
        if len(args) > 3:
            if action == "add":
                userid = user.replace("<@!", "").replace(">", "")
                touser = session.query(User).filter(User.userid == userid)[0]
                if not Utils.exists(session.query(Item).filter(Item.owner == touser.id, Item.name == itemName)):
                    item = Item()
                    item.owner = touser.id
                    item.amount = 0
                    item.name = str(itemName)
                    session.add(item)
                    session.commit()
                item = session.query(Item).filter(Item.owner == touser.id, Item.name == itemName)[0]
                item.amount += int(amount)
                session.commit()
                message = f"Вы успешно добавили предмет \"{item.name}\" x{amount} клиенту <@!{touser.userid}>"
            elif action == "remove":
                userid = user.replace("<@!", "").replace(">", "")
                touser = session.query(User).filter(User.userid == userid)[0]
                if not Utils.exists(session.query(Item).filter(Item.owner == touser.id, Item.name == itemName)):
                    item = Item()
                    item.owner = touser.id
                    item.amount = 0
                    item.name = itemName
                    session.add(item)
                    session.commit()
                item = session.query(Item).filter(Item.owner == touser.id, Item.name == itemName)[0]
                if item.amount >= 0 and item.amount - int(amount) >= 0:
                    item.amount -= int(amount)
                else:
                    message = f"Вы не можете отнять больше предметов чем есть у клиента"
                    embedColor = theme['error']
                    return False
                if item.amount == 0:
                    session.query(Item).filter_by(id=item.id).delete()
                session.commit()
                message = f"Вы успешно отняли предмет \"{item.name}\" x{amount} клиенту <@!{touser.userid}>"
            embed = Embed(color=embedColor)
            embed.add_field(name="Успех", value=message)
            await ctx.send(embed=embed)
    

bot.run(config['bot']['token'])