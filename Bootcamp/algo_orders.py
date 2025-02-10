# connect to exchange

import ccxt
import key_file as kf

kraken = ccxt.kraken({ 
'enableRateLimit': True,
'apiKey': 'kf.key["apiKey"]',
'secret': 'secret',

})

#get market data
#markets = kraken.load_markets()
#print(markets)


# get balance
#bal = kraken.fetch_balance()
#print(bal)

# making a order
