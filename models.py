from peewee import *
from db import dbhandle
import datetime

class BaseModel(Model):
    class Meta:
        database = dbhandle
 
 
class User(BaseModel):
    class Meta:
        db_table = "users"
        order_by = ('id',)

    id = PrimaryKeyField(null=False)
    userid = BigIntegerField(unique=True)
    balance = FloatField(default=0.0)

class Item(BaseModel):
    class Meta:
        db_table = "items"
        order_by = ('id',)

    id = PrimaryKeyField(null=False)
    owner = ForeignKeyField(User)
    name = CharField(max_length=64)
    amount = IntegerField(default=0)
    created = DateTimeField(default=datetime.datetime.now)

class Code(BaseModel):
    class Meta:
        db_table = "codes"
        order_by = ('id',)

    id = PrimaryKeyField(null=False)
    owner = ForeignKeyField(User)
    code = CharField(max_length=16)
    exp = DateTimeField(default=(datetime.datetime.now() + datetime.timedelta(days=1)))

class Settings(BaseModel):
    class Meta:
        db_table = "settings"
        order_by = ('id',)
    id = PrimaryKeyField(null=False)
    name = CharField(max_length=16)
    data = TextField()

class Storage(BaseModel):
    class Meta:
        db_table = "storages"
        order_by = ('id',)
    id = PrimaryKeyField(null=False)
    cells = IntegerField(default=1)
    coordinates = CharField(max_length=32)
    description = CharField(max_length=64)

class Order(BaseModel):
    class Meta:
        db_table = "orders"
        order_by = ('id',)

    id = PrimaryKeyField(null=False)
    status = CharField(max_length=16, default="WAIT")
    to_storage = ForeignKeyField(Storage)
    from_storage = ForeignKeyField(Storage)
    owner = ForeignKeyField(User)
    courier = ForeignKeyField(User, null=True)

class Cell(BaseModel):
    class Meta:
        db_table = "cells"
        order_by = ('id',)

    id = PrimaryKeyField(null=False)
    storage = ForeignKeyField(Storage)
    order = ForeignKeyField(Order, null=True)
    number = IntegerField(default=1)

dbhandle.connect()
dbhandle.create_tables([User, Item, Code, Settings, Order, Storage, Cell])