from db import engine, add_column, remove_column
from sqlalchemy import create_engine

from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime, time

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column('id', Integer, primary_key=True)
    userid = Column('userid', BigInteger, unique=True)
    balance = Column('balance', Float, default=0)

class Item(Base):
    __tablename__ = "items"

    id = Column('id', Integer, primary_key=True)
    owner = Column('owner', ForeignKey("users.id"))
    name = Column('name', String(64))
    amount = Column('amount', Integer, default=0)
    created = Column("created", DateTime, default=datetime.datetime.now)

class Code(Base):
    __tablename__ = "codes"

    id = Column('id', Integer, primary_key=True)
    owner = Column('owner', ForeignKey("users.id"))
    code = Column('code', String(64))
    exp = Column('expiration', DateTime, default=(datetime.datetime.now() + datetime.timedelta(days=1)), unique=True)

Base.metadata.create_all(bind=engine)

def make_session():
    newengine = create_engine("mysql+mysqldb://lovequiz_nextbot:234567-sS@lovequiz.beget.tech/lovequiz_nextbot?charset=utf8", echo=False)
    Session = sessionmaker(bind=newengine)

    session = Session()
    return session


def verify_code(code):
    session = make_session()
    code_instance = session.query(Code).filter(Code.code == code)
    if not Utils.exists(code_instance):
        return None
    if code_instance[0].exp < datetime.datetime.now():
        session.delete(code_instance[0])
        return None
    user = session.query(User).get(code_instance[0].owner)
    session.delete(code_instance[0])
    session.commit()
    return user


class Utils:
    def __init__(self):
        pass
    def exists(query):
        if not len(list(query)) > 0:
            return False
        return True

print(verify_code("123"))