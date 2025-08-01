
import requests

def get_trc20_transactions(address):
    url = f'https://apilist.tronscanapi.com/api/token_trc20/transfers?limit=20&start=0&sort=-timestamp&address={address}'
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers)
        return r.json().get('data', [])
    except:
        return []
