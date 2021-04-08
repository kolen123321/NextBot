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

dbhandle.connect()
User.create_table()
Item.create_table()
Code.create_table()
