class Validator:
    pass

class PingValidator(Validator):
    def __init__(self, ping):
        self.ping = ping
        data = ping.replace("<@!", "").replace(">", "")
        try:
            data = int(data)
        except:
            self.data = None
        self.data = data

class AmountValidator(Validator):
    def __init__(self, amount):
        self.amount = amount
        try:
            data = int(amount)
            if data < 0:
                data = None
        except:
            data = None
        self.data = data

class FloatAmountValidator(Validator):
    def __init__(self, amount):
        self.amount = amount
        try:
            data = float(amount)
            if data < 0:
                data = None
        except:
            data = None
        self.data = data