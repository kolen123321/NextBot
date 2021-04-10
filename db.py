from peewee import *
 
user = 'lovequiz_nextbot'
password = '234567-sS'
db_name = 'lovequiz_nextbot'
 
dbhandle = MySQLDatabase(
    db_name, user=user,
    password=password,
    host='lovequiz.beget.tech'
)

a = dbhandle.connect()
dbhandle.commit()
method_list = [func for func in dir(dbhandle) if callable(getattr(dbhandle, func))]
print(method_list)
dbhandle.close()