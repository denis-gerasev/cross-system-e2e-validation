
import requests

r = requests.get('https://api.binance.com/api/v3/ticker/bookTicker?symbol=BTCUSDT')

print (r.status_code)

data = r.json()



bidPrice = data['bidPrice']
askPrice = data['askPrice']


print (bidPrice)
print(askPrice)

