from peewee import *
 
user = 'lovequiz_nextbot'
password = '234567-sS'
db_name = 'lovequiz_nextbot'
 
dbhandle = MySQLDatabase(
    db_name, user=user,
    password=password,
    host='lovequiz.beget.tech'
)