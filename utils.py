import datetime
import json
from models import *



def verify_code(code):
    if code.exp < datetime.datetime.now():
        code.delete()
        return None
    return code.owner
    
def check_connection():
    """    global dbhandle
        if not dbhandle._state.closed:
            dbhandle.close()"""
    if dbhandle._state.closed:
        dbhandle.connect()


def close_connection():
    """    global dbhandle
        if not dbhandle._state.closed:
            dbhandle.close()
    """