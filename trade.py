import numpy as np
import trading_env as te

cangwei = False
balance = 10000
lots = 0.1
profit = 0
open_price = 0
close_price = 0
postion = te.TradingSim.posns

_action = ['buy','sell','wait','close_buy','close_sell']

if cangwei == False :
    action = np.random.choice(_action[:3])
    if action == 'buy':
        cangwei = True
        open_price = postion
    elif action == 'sell':
        open_price = postion
        cangwei = True
    else:
        pass
else:
    action = np.random.choice(_action[3:])

    if action == 'close_buy':
        close_price = postion
        profit = (close_price - open_price) * 10000 * lots
        cangwei = False
    elif action == 'close_sell':
        close_price = postion
        profit = (open_price - close_price) * 10000 * lots
        cangwei = False
    else:
        pass

if profit > 0 :
    reward = reward +1
    balance = balance + profit
else:
    balance = balance + profit
if balance > 20000:
    reward = reward + 1000




#print(action)