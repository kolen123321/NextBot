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
bot = commands.Bot(command_prefix="$", intents=intents)

bank_channel = 834499751289421855

bot.remove_command('help')


def incline_coin(number):
    if number == 1:
        return "NextCoin"
    elif number > 1:
        return "NextCoins"

def incline(number, word):
    if number == 1:
        return word
    elif number > 1:
        return word + "s"
    

def error(title="Error", message="Nothing"):
    embed=Embed(color=theme['error'])
    embed.add_field(name=title, value=message, inline=False)
    return embed

def info(title="Info", message="Nothing"):
    embed=Embed(color=theme['info'])
    embed.add_field(name=title, value=message, inline=False)
    return embed

def success(title="Success", message="Nothing"):
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
    embed.add_field(name="NextBank", value="Service", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="account", aliases=['a', 'acc'])
async def account(ctx):
    check_connection()
    if ctx.channel.id == config['channels']['nextbank']['client']:
        user = await create_or_get_user(ctx)
        embed=Embed(title=f"Account {ctx.author}", color=theme['info'])
        embed.add_field(name="Balance", value=f"{user.balance} {incline_coin(user.balance)}", inline=False)
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
            embed.add_field(name="Verification", value=f"Your verify code: {verify.code}", inline=False)
            message = await ctx.author.send(embed=embed)
            embed=Embed(color=theme['info'])
            embed.add_field(name="Verification", value=f"I sent the code to you in private messages", inline=False)
            await ctx.send(embed=embed)
    elif ctx.guild.get_role(config['roles']['banker']) in ctx.author.roles and ctx.channel.id == config['channels']['nextbank']['banker']:
        if len(args) == 1:
            user = await create_or_get_user(ctx)
            verify = Code.select().where(Code.code == args[0])
            if verify.exists():
                verify = Code.get(Code.code == args[0])
            else:
                await ctx.send(embed=error(message="Code is not found"))
                return False
            touser = verify_code(verify)
            embedColor = theme['info']
            if touser:
                title = "Verification"
                message = f"User: <@!{touser.userid}>"
            else:
                embedColor = theme['error']
                title = "Error"
                message = "The code was not found or expired"
            embed=Embed(color=embedColor)
            embed.add_field(name=title, value=message, inline=False)
            await ctx.send(embed=embed)
    close_connection()

@bot.command(name="help")
async def help(ctx):
    check_connection()
    if ctx.channel.id == 827989670541393920 or ctx.channel.id == bank_channel:
        embed=Embed(title=f"NextBank - help", color=theme['info'])
        embed.add_field(name="$help", value="Outputs this list", inline=False)
        embed.add_field(name="$account", value="Displays ifnormation about your account", inline=False)
        embed.add_field(name="$verify", value="Command to get verification code", inline=False)
        embed.add_field(name="$pay <Client> <Number of nextcoins>", value="Command to transfer nextcoins to the NextBank client", inline=False)
        embed.add_field(name="$give <Client> <Item name> <Number of items>", value="Command to transfer items to NextBank client", inline=False)
        embed.add_field(name="$inventory", value="Displays information about your things in the bank", inline=False)
    elif ctx.channel.id == 828200330969481248:
        embed=Embed(title=f"NextBank - help", color=theme['info'])
        embed.add_field(name="!help", value="Outputs this list", inline=False)
        embed.add_field(name="!manage <Action> <Client> <Number of nextcoins>", value="Team for bankers", inline=False)
        embed.add_field(name="!verify <Code>", value="Client verification command", inline=False)
        embed.add_field(name="<Actions>", value="add - adding an invoice, remove - reducing an invoice", inline=False)
        embed.add_field(name="<Client>", value="Client ping", inline=False)
        embed.add_field(name="<Number of nextcoins>", value="Number of nextcoins", inline=False)
    elif ctx.channel.id == config['channels']['nextdelivery']['client']:
        embed=Embed(title=f"NextDelivery - help", color=theme['info'])
        embed.add_field(name="!help", value="Outputs this list", inline=False)
        embed.add_field(name="!order <Warehouse from where> <Warehouse to where>", value="Command to create an order", inline=False)
        embed.add_field(name="!start <Order number>", value="Command to start an order after the start they write 1 NextCoin from you", inline=False)
        embed.add_field(name="!orders", value="Displays a list of your orders", inline=False)
        embed.add_field(name="!stores", value="Displays a list of NextDelivery warehouses")
    elif ctx.channel.id == config['channels']['nextdelivery']['notice']:
        embed=Embed(title=f"NextDelivery - help", color=theme['info'])
        embed.add_field(name="!help", value="Outputs this list", inline=False)
        embed.add_field(name="!accept <Order number>", value="Command to accept the order", inline=False)
        embed.add_field(name="!delivery <Order number>", value="Command to place an order", inline=False)
        embed.add_field(name="!orders", value="Displays a list of your accepted orders", inline=False)
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
                await ctx.send(embed=error(message="The value of <Count NextCoins> is entered incorrectly"))
                return False
            if not touserid:
                await ctx.send(embed=error(message="The value <Client> is entered incorrectly"))
                return False
            touser = User.select().where(User.userid == touserid)
            if not touser.exists():
                await ctx.send(embed=error(message="Client not found"))
                return False
            touser = User.select().where(User.userid == touserid).first()
            user.balance -= amount
            touser.balance += amount
            touser.save()
            user.save()
            title = "Success"
            message = f"You have successfully transferred {amount} {incline_coin(amount)} to <@!{touser.userid}>"
        else:
            embedColor = theme['info']
            title = "Command"
            message = f"!pay <Client> <Count NextCoin-ов>\n\nExample: !pay <@!708326089440886836> 10"
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
        embed.add_field(name='NextCoin', value=f'1 NextCoin = {cours} {incline(cours, "diamond")}', inline=False)
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
                    await ctx.send(embed=error(message="Client is not found"))
                    return False
                touser = touser.first()
                touser.balance += float(amount)
                touser.save()
                title = "success"
                message = f"You have successfully added {amount} {incline_coin(amount)} to <@!{touser.userid}>"
            elif action == "remove":
                userid = user.replace("<@!", "").replace(">", "")
                touser = User.select().where(User.userid == userid)
                amount = diamonds
                amount_pr = float(amount) + (float(amount) / 100 * 5)
                if not touser.exists():
                    await ctx.send(embed=error(message="Client is not found"))
                    return False
                touser = touser.first()
                if touser.balance - amount_pr > 0:
                    amount = amount_pr
                touser.balance -= float(amount)
                touser.save()
                title = "Успех"
                message = f"You have successfully taken away {amount} {incline_coin(amount)} from <@!{touser.userid}>"
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
            await ctx.send(embed=error(message="The warehouse <Where> is full, please try again later"))
            return False
        if not from_cell:
            await ctx.send(embed=error(message="The warehouse <From Where> is full, please try again later"))
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
        await ctx.send(embed=success(message=f"You have successfully created an order, cell <From>: {from_cell.number} box <to>: {to_cell.number}\nAfter you put the item(s), write:\n!start {order.id}"))
        close_connection()

@bot.command(name="storages")
async def storages(ctx):
    if ctx.channel.id == config['channels']['nextdelivery']['client']:
        storages = Storage.select().where(1)
        storages_in_str = ""
        for s in storages:
            storages_in_str += f"№{s.id} description: {s.description} coordinates: {s.coordinates}\n"
        await ctx.send(embed=info(title="Storages NextDelivery", message=f"{storages_in_str}"))

@bot.command(name="orders")
async def orders(ctx, *args):
    if ctx.channel.id == config['channels']['nextdelivery']['client']:
        check_connection()
        user = await create_or_get_user(ctx)
        orders = Order.select().where(Order.owner == user)
        orders_in_str = ""
        for o in orders:
            if o.status == "WAIT":
                status = "Wait items"
            elif o.status == "STARTED":
                status = "Wait deliveryman"
            elif o.status == "DELIVERY":
                status = "Wait delivery"
            to_cell = Cell.get((Cell.order == o) & (Cell.storage == o.to_storage))
            from_cell = Cell.get((Cell.order == o) & (Cell.storage == o.from_storage))
            orders_in_str += f"№{o.id} status: {status} box \"From\": {from_cell.number} \"To\": {to_cell.number}\n"
        if len(orders_in_str) <= 0:
            orders_in_str = "Empty..."
        await ctx.send(embed=info(title="Your orders",message=f"{orders_in_str}"))
        close_connection()
    elif ctx.channel.id == config['channels']['nextdelivery']['notice']:
        check_connection()
        user = await create_or_get_user(ctx)
        orders = Order.select().where(Order.courier == user)
        orders_in_str = ""
        for o in orders:
            to_cell = Cell.get((Cell.order == o) & (Cell.storage == o.to_storage))
            from_cell = Cell.get((Cell.order == o) & (Cell.storage == o.from_storage))
            orders_in_str += f"#{o.id} box \"From\": {from_cell.number} \"To\": {to_cell.number}\n"
        if len(orders_in_str) <= 0:
            orders_in_str = "Empty..."
        await ctx.send(embed=info(title="Your orders", message=f"{orders_in_str}"))
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
            await ctx.send(embed=error(message="Order is not found"))
            return False
        except ValueError:
            await ctx.send(embed=error(message="Value <Number of order> entered incorrect"))
            return False
        if order.status != "WAIT":
            await ctx.send(embed=error(message="Order is already created"))
            return False
        delivery_price = 1
        if user.balance >= delivery_price:
            user.balance -= delivery_price
            user.save()
        else:
            await ctx.send(embed=error(message="You don't have enough funds"))
            return False
        order.status = "STARTED"
        order.save()
        to_cell = Cell.get((Cell.order == order) & (Cell.storage == order.to_storage))
        from_cell = Cell.get((Cell.order == order) & (Cell.storage == order.from_storage))
        await ctx.send(embed=success(message="Order is created"))
        from_storage = from_cell.storage.id
        to_storage = to_cell.storage.id
        await courier_notice_channel.send(embed=info(title="New order", message=f"Box <from>: {from_storage} {from_cell.number} box <to>: {to_storage} {to_cell.number}\nIn order to accept the order, please register:\n!accept {order.id}"))
        close_connection()

@bot.command(name="accept")
async def start(ctx, *args):
    if ctx.channel.id == config['channels']['nextdelivery']['notice']:
        check_connection()
        user = await create_or_get_user(ctx)
        try:
            order = Order.get(int(args[0]))
        except peewee.DoesNotExist:
            await ctx.send(embed=error(message="Order not found"))
            return False
        except ValueError:
            await ctx.send(embed=error(message="The value <Order number> is entered incorrectly"))
            return False
        if order.courier:
            await ctx.send(embed=error(message="The order has already been taken"))
            return False
        if order.status == "WAIT":
            await ctx.send(embed=error(message="The order has not reached the required stage yet"))
            return False
        to_user = order.owner.userid
        to_user = discord.utils.get(ctx.guild.members, id=to_user)
        order.status = "DELIVERY"
        order.courier = user
        order.save()
        await to_user.send(embed=info(title="NextDelivery Notification", message=f"Your order No.{order.id } was taken by courier<@!{user.userid}>"))
        await ctx.send(embed=success(message=f"You have successfully taken the order #{order.id}"))
        close_connection()

@bot.command(name="delivery")
async def start(ctx, *args):
    if ctx.channel.id == config['channels']['nextdelivery']['notice']:
        check_connection()
        user = await create_or_get_user(ctx)
        try:
            order = Order.get(int(args[0]))
        except peewee.DoesNotExist:
            await ctx.send(embed=error(message="Order not found"))
            return False
        except ValueError:
            await ctx.send(embed=error(message="The value <Order number> is entered incorrectly"))
            return False
        if order.courier != user:
            await ctx.send(embed=error(message="You are not the courier of this order"))
            return False
         if order.status == "STARTED":
            await ctx.send(embed=error(message="The order has not reached the required stage yet"))
            return False
        to_user = order.owner.userid
        to_user = discord.utils.get(ctx.guild.members, id=to_user)
        await to_user.send(embed=info(title="NextDelivery Notification", message=f"Your order No.{order.id } was delivered by courier<@!{user.userid}>"))
        await ctx.send(embed=success(message=f"You have successfully delivered order #{order.id}"))
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
