from sqlalchemy import create_engine

engine = create_engine("mysql+mysqldb://lovequiz_nextbot:234567-sS@lovequiz.beget.tech/lovequiz_nextbot?charset=utf8", echo=False)

def add_column(table_name, column):
    global engine
    column_name = column.compile(dialect=engine.dialect)
    column_type = column.type.compile(engine.dialect)
    engine.execute('ALTER TABLE %s ADD COLUMN %s %s' % (table_name, column_name, column_type))

def remove_column(table_name, column_name):
    global engine
    engine.execute(f'ALTER TABLE {table_name} DROP COLUMN {column_name}')

