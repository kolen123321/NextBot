import datetime
import requests
import json


class QiwiApi:
    def __init__(self, secret_key, public_key):
        self.pub_key = public_key
        self.secret_key = secret_key
        self.default_headers = {
            'content-type': 'application/json',
            'accept': 'application/json',
            'authorization': 'Bearer ' + self.secret_key
        }

    def create_invoice(self, unique_id, days, customer=None, amount=1):
        date = datetime.datetime.now() + datetime.timedelta(days=days)
        date_str = date.strftime("%Y-%m-%dT%H:%M:%S+03:00")

        data = {
            'amount': {
                'currency': 'RUB',
                'value': amount,
            },
            'expirationDateTime': date_str,
            'customer': customer,
            'comment': 'Пополнение баланса NextLevel для DanielGrash'
        }
        r = requests.put(f'https://api.qiwi.com/partner/bill/v1/bills/{unique_id}/', data=json.dumps(data), headers=self.default_headers)
        return r.json()
    
    def check_invoice(self, unique_id):
        r = requests.get(f'https://api.qiwi.com/partner/bill/v1/bills/{unique_id}', headers=self.default_headers)
        return r.json()

    def reject_invoice(self, unique_id):
        r = requests.get(f'https://api.qiwi.com/partner/bill/v1/bills/{unique_id}/reject', headers=self.default_headers)
        return r.json()